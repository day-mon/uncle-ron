import logging
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.config import get_env_file_path


class AppSettings(BaseSettings):
    token: str = ""
    openrouter_api_key: str = ""
    openai_api_key: str | None = None
    prefix: str = "$"
    cogs_dir: str = "app/cogs"
    disabled_cogs: list[str] = []
    default_model: str = "openai/gpt-5-mini"
    fact_check_model: str = "perplexity/sonar"
    qotd_model: str = "x-ai/grok-beta"

    # Database settings
    reset_database: bool = False

    # Logging settings
    log_level: int = logging.INFO
    discord_log_level: int = logging.WARNING
    aiosqlite_log_level: int = logging.ERROR

    model_config = SettingsConfigDict(
        env_file=get_env_file_path(cfg_type="app"),
        case_sensitive=False,
    )

    @property
    def cogs(self) -> list[str]:
        """Return a list of cog module import paths, excluding __pycache__ and disabled ones."""
        base_path = Path(self.cogs_dir)
        cogs = []
        for file in base_path.glob("*.py"):
            if file.name == "__init__.py":
                continue
            module_name = f"{self.cogs_dir.replace('/', '.')}.{file.stem}"
            if module_name not in self.disabled_cogs:
                cogs.append(module_name)
        return cogs


settings = AppSettings()
