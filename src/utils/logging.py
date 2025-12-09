"""Logging configuration for Discord Gemini Bot."""

import logging
import sys


class StdoutStderrHandler(logging.Handler):
    """Route INFO/DEBUG/WARNING to stdout, ERROR/CRITICAL to stderr."""

    def __init__(self) -> None:
        super().__init__()
        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def emit(self, record: logging.LogRecord) -> None:
        stream = sys.stderr if record.levelno >= logging.ERROR else sys.stdout
        stream.write(self.format(record) + "\n")
        stream.flush()


def setup_logging() -> None:
    """Configure logging for the entire application."""
    handler = StdoutStderrHandler()

    # Configure root logger to affect all loggers (including discord.py)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()  # Remove default handlers
    root_logger.addHandler(handler)


def get_logger(name: str = "GeminiBot") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Configure logging on import
setup_logging()

# Default logger instance
logger = get_logger()
