import json
import logging
from contextvars import ContextVar

# Holds the current request's ID, so any function can log it without passing it around
request_id_var: ContextVar[str] = ContextVar("request_id", default="-") # Variable that holds a different value per request

logger = logging.getLogger("hr_triage") # Our own name logger


class JsonFormatter(logging.Formatter): # Decides what one log line looks like
    """Turn every log record into one JSON line."""

    def format(self, record):
        entry = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "event": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        entry.update(getattr(record, "fields", {}))
        return json.dumps(entry, ensure_ascii=False)


def setup_logging():
    """Send our logs to the terminal as JSON. Safe to call more than once."""
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def log_event(event: str, level: int = logging.INFO, **fields): # The one function to actually call
    """Log one event with extra fields, e.g. log_event("ticket_saved", ticket_id=12)."""
    logger.log(level, event, extra={"fields": fields})