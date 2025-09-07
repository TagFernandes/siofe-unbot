# Metricas
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



## Log
import logging
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler

#Log
handler = LokiLoggerHandler(
    url="http://localhost:3100/loki/api/v1/push",
    labels={"application": "SIOFE", "environment": "development"},
)
logger = logging.getLogger("siofe-unbot-logger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)