## Log
import logging
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler
import sys
import traceback

#Log
handler = LokiLoggerHandler(
    url="http://localhost:3100/loki/api/v1/push",
    labels={"application": "SIOFE", "environment": "development"},
)
logger = logging.getLogger("siofe-unbot-logger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

from prometheus_client import (
    Gauge
)

VERIFICACAO_OFERTA_PROCESS = Gauge(
    'verificacao_oferta_process',
    'Mostra se a aplicação está executando verificação de ofertas'
)

COMECO_EXTRACAO_OFERTA = Gauge(
    'comeco_extracao_oferta_debug',
    'Timestamp Unix do comeco da verficacao oferta.'
)

ARQUIVO_OFERTA_ULTIMA_GERACAO_TIMESTAMP = Gauge(
    'ULTIMA_GERACAO_OFERTA_TIMESTAMP',
    'Timestamp Unix da última vez que o arquivo de ofertas foi gerado com sucesso.'
)

def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """
    Função que será chamada para qualquer exceção não tratada.
    Ela loga o erro usando nosso logger configurado antes de terminar.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Não loga o erro se o usuário apertou Ctrl+C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    traceback_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
    formatted_traceback = "".join(traceback_list)

    logger.critical(
        f"Exceção não tratada capturada | {exc_type} | {exc_value}  | \n-----------------\n   {formatted_traceback}   \n-----------------\n",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
sys.excepthook = handle_unhandled_exception