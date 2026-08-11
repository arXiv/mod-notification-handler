"""logging setup shared by all jobs"""
import json
import logging

from app.shared.config import settings


class _GCPFormatter(logging.Formatter):
    """Emit structured JSON so GCP Cloud Logging picks up the correct severity."""

    _SEVERITY = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        return json.dumps({
            "severity": self._SEVERITY.get(record.levelno, "DEFAULT"),
            "message": message,
            "logger": record.name,
        })


def setup_logging() -> None:
    """configure the root logger for GCP. call once at job startup"""
    handler = logging.StreamHandler()
    handler.setFormatter(_GCPFormatter())
    logging.root.setLevel(settings.LOG_LEVEL)
    logging.root.addHandler(handler)
