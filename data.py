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