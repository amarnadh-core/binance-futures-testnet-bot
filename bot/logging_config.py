"""Logging configuration for file and console output."""

import logging
from pathlib import Path


def configure_logging(log_file: Path | None = None) -> logging.Logger:
    logger = logging.getLogger("trading_bot")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    target = log_file or Path(__file__).resolve().parents[1] / "logs" / "trading_bot.log"
    target.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(target, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

