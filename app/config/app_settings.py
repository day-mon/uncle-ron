import logging
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.config import get_env_file_path


class FeatureMapping(BaseModel):
    """Pydantic model for feature mapping configuration."""
    ai: str = "ai_enabled"
    factcheck: str = "fact_check_enabled"
    grok: str = "grok_enabled"
    qotd: str = "qotd_enabled"

    def get_mapping_dict(self) -> dict[str, str]:
        """Return the feature mapping as a dictionary."""
        return {
            "ai": self.ai,
            "factcheck": self.factcheck,
            "grok": self.grok,
            "qotd": self.qotd,
        }


class FeatureNames(BaseModel):
    """Pydantic model for feature display names."""
    ai: str = "AI Ask Command"
    factcheck: str = "Fact Check"
    grok: str = "Grok AI"
    qotd: str = "Question of the Day"

    def get_names_dict(self) -> dict[str, str]:
        """Return the feature names as a dictionary."""
        return {
            "ai": self.ai,
            "factcheck": self.factcheck,
            "grok": self.grok,
            "qotd": self.qotd,
        }


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

    reset_database: bool = False

    # Developer settings
    developer_ids: list[int] = []

    # Logging settings
    log_level: int = logging.INFO
    discord_log_level: int = logging.WARNING
    aiosqlite_log_level: int = logging.ERROR

    # Feature configuration
    feature_mapping: FeatureMapping = FeatureMapping()
    feature_names: FeatureNames = FeatureNames()

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
