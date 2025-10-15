import logging
import sys
from pathlib import Path

# ANSI color codes for pretty terminal output
COLORS = {
    "RESET": "\033[0m",
    "BLACK": "\033[30m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
    "BG_BLACK": "\033[40m",
    "BG_RED": "\033[41m",
    "BG_GREEN": "\033[42m",
    "BG_YELLOW": "\033[43m",
    "BG_BLUE": "\033[44m",
    "BG_MAGENTA": "\033[45m",
    "BG_CYAN": "\033[46m",
    "BG_WHITE": "\033[47m",
}

# Emoji prefixes for different log levels
LEVEL_PREFIXES = {
    "DEBUG": "🔍",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🔥",
}

# Color mapping for different log levels
LEVEL_COLORS = {
    "DEBUG": COLORS["CYAN"],
    "INFO": COLORS["GREEN"],
    "WARNING": COLORS["YELLOW"],
    "ERROR": COLORS["RED"],
    "CRITICAL": COLORS["BG_RED"] + COLORS["WHITE"] + COLORS["BOLD"],
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors and emojis to log messages"""

    def __init__(self, fmt: str | None = None, datefmt: str | None = None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        # Save original values
        levelname = record.levelname
        name = record.name
        message = record.getMessage()

        # Add color and emoji to level name
        level_color = LEVEL_COLORS.get(levelname, COLORS["RESET"])
        level_prefix = LEVEL_PREFIXES.get(levelname, "")

        # Format the record with colors
        record.levelname = f"{level_color}{level_prefix} {levelname}{COLORS['RESET']}"
        record.name = f"{COLORS['BLUE']}{COLORS['BOLD']}{name}{COLORS['RESET']}"

        # Format the message
        formatted_msg = super().format(record)

        # Restore original values
        record.levelname = levelname
        record.name = name

        return formatted_msg


def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    module_levels: dict[str, int] | None = None,
) -> None:
    """
    Set up logging with pretty formatting

    Args:
        level: The base logging level
        log_file: Optional file path to write logs to
        module_levels: Dict of module names and their specific log levels
    """
    # Create formatters
    console_formatter = ColoredFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

    # Set specific module levels
    if module_levels:
        for module, module_level in module_levels.items():
            logging.getLogger(module).setLevel(module_level)

    # Set lower levels for some noisy libraries
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name

    Args:
        name: The name of the logger

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
