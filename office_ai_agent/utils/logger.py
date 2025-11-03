import logging
import os
from typing import Optional


_LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def get_logger(name: str, level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """Return a configured logger.

    Respects LOG_LEVEL environment variable if `level` not provided.
    Optionally writes to a file in addition to stderr.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # Determine level
    lvl_name = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    lvl = _LEVEL_MAP.get(lvl_name, logging.INFO)

    logger.setLevel(lvl)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
