import os

metrics_dir = "/tmp/prometheus_data_siofe"
os.environ['PROMETHEUS_MULTIPROC_DIR'] = metrics_dir
os.makedirs(metrics_dir, exist_ok=True)

from flask import Flask, request, jsonify, g ,Response
import time
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
from prometheus_flask_exporter import PrometheusMetrics
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
FlaskInstrumentor().instrument_app(app, excluded_urls="/metrics")
metrics = PrometheusMetrics(app, path=None)



#Metricas
from prometheus_client import (
    Counter, Gauge, Histogram, 
    generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, generate_latest
)
from prometheus_client.multiprocess import MultiProcessCollector


#
if os.environ.get("PROMETHEUS_MULTIPROC_DIR") is None:
    print(f"Atenção! A variável de ambiente metricas NÃO foi encontrada.")
    logger.error("Atenção! A variável de ambiente metricas NÃO foi encontrada.")
###################################################################################

@app.route('/metrics')
def metrics():
    """
    Agrega as métricas de todos os processos Gunicorn e as expõe.
    """
    from prometheus_client import CollectorRegistry, generate_latest
    from prometheus_client.multiprocess import MultiProcessCollector
    # Cria um registro para coletar as métricas
    registry = CollectorRegistry()
    # Adiciona o coletor multiprocesso que lê os arquivos do diretório
    MultiProcessCollector(registry)
    # Gera a saída no formato de texto que o Prometheus entende
    data = generate_latest(registry)
    return Response(data, mimetype='text/plain; version=0.0.4; charset=utf-8')


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