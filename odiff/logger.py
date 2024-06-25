from logging import INFO, Logger

from colorlog import (
    ColoredFormatter,
    StreamHandler,
    getLogger,
)

G_HANDLER = StreamHandler()
G_HANDLER.setFormatter(
    ColoredFormatter(
        "%(log_color)s[%(levelname).4s:%(name)s]%(reset)s %(message)s",
    )
)


VALID_LOG_LEVELS = [
    "CRITICAL",
    "FATAL",
    "ERROR",
    "WARNING",
    "WARN",
    "INFO",
    "DEBUG",
    "NOTSET",
]

DEFAULT_LOG_LEVEL = INFO


def set_default_log_level(level: int):
    global DEFAULT_LOG_LEVEL
    DEFAULT_LOG_LEVEL = level


def get_logger(name: str, handler: StreamHandler = G_HANDLER) -> Logger:
    log: Logger = getLogger(name)
    log.addHandler(handler)
    return log
