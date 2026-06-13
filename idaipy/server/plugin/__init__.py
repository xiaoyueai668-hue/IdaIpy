import json
import logging
import os
import sys

from . import config as _cfg

TAG = "[IdaIpy]"

# ── Log directory ──────────────────────────────────────────────────────────

_IDAIPY_LOG_DIR = os.environ.get(
    "IDAIPY_LOG_DIR",
    os.path.expanduser("~/.idaipy")
)

_log_file_path = os.path.join(_IDAIPY_LOG_DIR, "idaipy.log")
_file_handler = None
_json_logger = None


def _setup_logging():
    """Configure file-based JSON logging to ~/.idaipy/idaipy.log."""
    global _file_handler, _json_logger

    try:
        os.makedirs(_IDAIPY_LOG_DIR, exist_ok=True)
        _file_handler = logging.FileHandler(_log_file_path)
        _file_handler.setFormatter(logging.Formatter("%(message)s"))
        _json_logger = logging.getLogger("idaipy_json")
        _json_logger.addHandler(_file_handler)
        _json_logger.setLevel(logging.INFO)
        _json_logger.propagate = False
    except Exception:
        _file_handler = None
        _json_logger = None


_setup_logging()


def log(msg: str) -> None:
    """Always print to IDA Output (human-readable)."""
    print(f"{TAG} {msg}")


def dbg(msg: str) -> None:
    """Only print when DEBUG is True."""
    if _cfg.DEBUG:
        print(f"{TAG} [DBG] {msg}")


def log_json(event: str, **kwargs) -> None:
    """Log a structured JSON event to file, and human-readable to IDA Output.

    Args:
        event: Event name (e.g., "connect", "exec", "error")
        **kwargs: Additional fields to include in the JSON record
    """
    record = {"event": event, **kwargs}

    # Print human-readable summary to IDA Output
    if event == "exec":
        print(f"{TAG} exec mode={kwargs.get('mode')} "
              f"code_len={kwargs.get('code_len')} "
              f"duration_ms={kwargs.get('duration_ms')}")
    elif event == "connect":
        print(f"{TAG} Client connected: {kwargs.get('peer')}")
    elif event == "disconnect":
        print(f"{TAG} Client disconnected: {kwargs.get('peer')}")
    elif event == "error":
        print(f"{TAG} ERROR {kwargs.get('error_type')}: "
              f"{kwargs.get('error_message')}")
    elif event == "auth_success":
        print(f"{TAG} Auth success for peer: {kwargs.get('peer')}")
    elif event == "auth_failure":
        print(f"{TAG} Auth failure for peer: {kwargs.get('peer')}")
    elif event == "shutdown":
        print(f"{TAG} Server shutdown requested")
    else:
        print(f"{TAG} {event}")

    # Write JSON to file
    if _json_logger:
        try:
            _json_logger.info(json.dumps(record, ensure_ascii=False))
        except Exception:
            # Graceful degradation: if JSON logging fails, don't break functionality
            pass
