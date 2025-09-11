from flask import Flask, request, jsonify, g ,Response
import time
import os
import json
from functools import wraps
import threading
from datetime import datetime

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
##
from data import logger
##
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
FlaskInstrumentor().instrument_app(app)



#Metricas
from prometheus_client import (
    Counter, Gauge, Histogram, 
    generate_latest, CONTENT_TYPE_LATEST
)

#Metricas
REQUESTS_TOTAL = Counter(
    'flask_requests_total',
    'Total de requisições HTTP processadas.',
    ['method', 'endpoint', 'status_code']
)

ERRORS_TOTAL = Counter(
    'flask_errors_total',
    'Total de erros encontrados na aplicação.',
    ['error_type', 'endpoint']
)
REQUESTS_IN_PROGRESS = Gauge(
    'flask_requests_in_progress',
    'Número de requisições em progresso.',
    ['endpoint']
)

REQUEST_LATENCY = Histogram(
    'flask_request_latency_seconds',
    'Latência das requisições HTTP.',
    ['endpoint'],
    buckets=[0.1, 0.2, 0.5, 1, 2, 5]
)
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


@app.route('/timeOferta', methods=['GET'])
def sendTimeOferta():
    with open("time.json", 'r', encoding='utf-8') as arquivo:
        dados = json.load(arquivo)
    logger.info(f"Solicitacao de tempo de thread | tempo de: {dados["time"]} seg")
    return str(dados["time"])



@app.route('/timeOferta', methods=['POST'])
def setTimeOferta():
    logger.info("Solicitacao para set de tempoOferta")
    dados_requisicao = request.get_json()
    tempo = dados_requisicao.get("tempo")
    tokenRequisicao = dados_requisicao.get("token")

    if not tempo or not tokenRequisicao:
        logger.warning("Requisicao de set tempoOferta mal formatada")
        return jsonify({
            'erro': 'Os campos "tempo" e "token" são obrigatórios.'
        }), 400

    try:
        with open("token.json", 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
            token = dados["token"]

    except Exception as e:
        logger.error(f"Erro ao obter token do servidor: {e}")
        return "Erro nos servidor", 500
    

    if tokenRequisicao != token:
        logger.warning(f"Token inválido: {tokenRequisicao}")
        return jsonify({
            'erro': 'token inválido'
        }), 403
    
    try:
        tempo = int(tempo)
    except:
        logger.warning("Nao foi possivel converter o tempo de setTimeOferta para inteiro")
        return jsonify({
            'erro': 'tempo deve ser um inteiro'
        }), 400
    
    dados = {"time":tempo}
    with open("time.json", 'w', encoding='utf-8') as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False) 
    logger.info(f"Tempo setOferta para: {tempo}")

    return f"Tempo configurado com sucesso ({tempo})", 200
    

@app.route('/timeOfertaTimeStamp/<timestamp>')
def converter_timestamp(timestamp):
    """
    Esta função é acionada quando a URL /converter/<timestamp> é acessada.
    Ela recebe o timestamp da URL, converte para uma data e retorna o resultado.
    """
    try:
        data_hora = datetime.fromtimestamp(float(timestamp))
        
        # Formata o objeto datetime para uma string legível (Dia/Mês/Ano Hora:Minuto:Segundo)
        data_formatada = data_hora.strftime('%d/%m/%Y %H:%M:%S')
        
        return data_formatada
    except:
        return "Erro ao obter timestamp", 500
##############################################################################################################
oferta = threading.Thread(target=Lista_Oferta.main)
oferta.daemon = True
oferta.start()
print("Serivdor iniciado")
logger.info("Servidor iniciado")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)