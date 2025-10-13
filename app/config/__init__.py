import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

environment = os.getenv("ENVIRONMENT", "development")


def get_resources_dir() -> Path:
    """
    Returns the absolute path to the `resources` directory,
    no matter where this function is called from.
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "resources"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("Could not locate `resources` directory.")


def get_env_file_path(cfg_type: str) -> tuple[str, str]:
    """
    Returns the possible env file paths for a given config type.
    """
    base = get_resources_dir() / "env"
    logger.debug(f"base: {base}")
    other_parts = (
        str(base / f".{cfg_type}.env"),
        str(base / f".{cfg_type}.{environment}.env"),
    )
    logger.debug(f"other_parts: {other_parts}")
    return other_parts
