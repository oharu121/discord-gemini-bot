"""Logging configuration for Discord Gemini Bot."""

import logging
import sys


def setup_logger(name: str = "GeminiBot") -> logging.Logger:
    """Configure and return a logger instance."""
    # Use stdout instead of stderr so logs appear normal (not red) in Railway
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    return logging.getLogger(name)


# Default logger instance
logger = setup_logger()
