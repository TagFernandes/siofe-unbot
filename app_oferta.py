from flask import Flask, request, jsonify, g ,Response
import time
import os
import json
from functools import wraps
import threading

from werkzeug.utils import secure_filename

import Lista_Oferta

# 1. --- Imports do OpenTelemetry ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor # A biblioteca chave

#Trace
resource = Resource(attributes={
    "service.name": "siofe-unbot",
    "service.version": "0.1.0"
})
tracer_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
FlaskInstrumentor().instrument_app(app)

#Metricas
from data import (
    REQUESTS_TOTAL, ERRORS_TOTAL, REQUESTS_IN_PROGRESS, REQUEST_LATENCY, logger
)
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
###################################################################################


@app.before_request
def before_request():
    """Executado antes de cada requisição."""
    # Armazena o tempo de início no objeto 'g' do Flask, que é específico para cada requisição
    g.start_time = time.time()
    # Incrementa o gauge de requisições em progresso para o endpoint atual
    REQUESTS_IN_PROGRESS.labels(endpoint=request.path).inc()

@app.after_request
def after_request(response):
    """Executado após cada requisição."""
    # Calcula a latência
    latency = time.time() - g.start_time
    # Observa a latência no histograma, com a label do endpoint
    REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    
    # Decrementa o gauge de requisições em progresso
    REQUESTS_IN_PROGRESS.labels(endpoint=request.path).dec()
    
    # Incrementa o contador de requisições totais
    REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=request.path,
        status_code=response.status_code
    ).inc()
    
    return response

@app.route('/metrics')
def metrics():
    """Expõe as métricas no formato do Prometheus."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


############################################################################################################
@app.route('/oferta', methods=['GET'])
def get_oferta_json():
    """
    Endpoint para ler um arquivo de oferta com base no ano e semestre
    e retornar seu conteúdo como uma resposta JSON.

    Query Parameters:
        ano (str): O ano da oferta.
        semestre (str): O semestre da oferta.

    Returns:
        JSON: O conteúdo do arquivo de oferta correspondente ou uma mensagem de erro.
    """
    OFERTAS_DIRECTORY = 'ofertas'

    ano = request.args.get('ano')
    semestre = request.args.get('semestre')

    # --- Tratamento de Erros: Verifica se os parâmetros foram fornecidos ---
    if not ano and not semestre:
        data = Lista_Oferta.obter_ano_e_semestre_personalizado()
        ano = str(data['ano'])
        semestre = str(data['semestre'])
    elif not ano or not semestre:
        return jsonify({"erro": "Informe corretamente os campos ano e semestre."}), 400

    # --- Segurança: Constrói o nome do arquivo de forma segura ---
    nome_arquivo = f"oferta_{secure_filename(ano)}_{secure_filename(semestre)}.json"
    
    # Constrói o caminho completo e seguro para o arquivo
    caminho_arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), OFERTAS_DIRECTORY, nome_arquivo)

    try:
        # --- Leitura do Arquivo e Retorno como JSON ---
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            # Carrega o conteúdo do arquivo JSON para um dicionário Python
            dados = json.load(f)
        
        # Usa a função jsonify do Flask para retornar os dados
        # com o cabeçalho 'Content-Type: application/json' correto.
        return Response(
            json.dumps(dados, ensure_ascii=False),
            mimetype="application/json; charset=utf-8"
        )

    except FileNotFoundError:
        # --- Tratamento de Erros: Arquivo não encontrado ---
        logger.warning(f"O arquivo de oferta para o ano {ano} e semestre {semestre} não foi encontrado.")
        return jsonify({"erro": f"O arquivo de oferta para o ano {ano} e semestre {semestre} não foi encontrado."}), 404
    except json.JSONDecodeError:
        # --- Tratamento de Erros: JSON inválido ---
        logger.error(f"O arquivo '{nome_arquivo}' contém um JSON inválido.")
        return jsonify({"erro": f"O arquivo '{nome_arquivo}' contém um JSON inválido."}), 500


##############################################################################################################
oferta = threading.Thread(target=Lista_Oferta.main)
oferta.daemon = True
oferta.start()
logger.info("Thread de oferta iniciada")

print("Serivdor iniciado")
logger.info("Servidor iniciado")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)