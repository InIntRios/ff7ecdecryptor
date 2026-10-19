"""
Centralized Logging Infrastructure
Provides console, file, and graphical UI event streaming handlers.
"""

import sys
import logging
from typing import Optional, Callable
from ff7ec.constants import LOG_FILE


class UILogHandler(logging.Handler):
    """Custom logging handler forwarding log events to an interactive UI callback."""
    def __init__(self, log_callback: Callable[[str, str], None]):
        super().__init__()
        self.log_callback = log_callback

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.log_callback(record.levelname, msg)
        except Exception:
            pass


def setup_logger(callback: Optional[Callable[[str, str], None]] = None) -> logging.Logger:
    """Configures and returns the central logger for FF7EC Decryptor."""
    logger = logging.getLogger("FF7EC_Extractor")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_fmt = logging.Formatter("[%(levelname)s] %(message)s")

    # Console stream handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(console_fmt)
    logger.addHandler(ch)

    # Persistent log file handler
    try:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
        fh.setLevel(logging.INFO)
        fh.setFormatter(file_fmt)
        logger.addHandler(fh)
    except Exception:
        pass

    # UI stream handler
    if callback:
        uh = UILogHandler(callback)
        uh.setLevel(logging.INFO)
        uh.setFormatter(console_fmt)
        logger.addHandler(uh)

    return logger
