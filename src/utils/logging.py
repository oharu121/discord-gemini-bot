"""Logging configuration for Discord Gemini Bot."""

import logging


def setup_logger(name: str = "GeminiBot") -> logging.Logger:
    """Configure and return a logger instance."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(name)


# Default logger instance
logger = setup_logger()
