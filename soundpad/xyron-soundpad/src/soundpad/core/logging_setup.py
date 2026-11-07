import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured = False


def configure_logging(logs_dir: Path, level: int = logging.INFO) -> None:
    global _configured
    root = logging.getLogger()
    if _configured:
        return
    root.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)

    logs_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        logs_dir / "soundpad.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    sys.excepthook = _log_unhandled
    _configured = True


def reset_logging() -> None:
    global _configured
    root = logging.getLogger()
    for handler in list(root.handlers):
        handler.close()
        root.removeHandler(handler)
    _configured = False


def _log_unhandled(exc_type, exc_value, exc_traceback) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger("soundpad").critical(
        "Excepción no controlada", exc_info=(exc_type, exc_value, exc_traceback)
    )
