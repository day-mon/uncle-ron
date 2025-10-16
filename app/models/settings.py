from pydantic import BaseModel
from functools import cached_property


class FeatureSetting(BaseModel):
    """Pydantic model for individual feature settings."""
    short_name: str
    description: str
    value: str


class FeatureSettings(BaseModel):
    """Pydantic model for all feature settings with cached property access."""
    
    @cached_property
    def features(self) -> list[FeatureSetting]:
        """Return the list of all feature settings."""
        return [
            FeatureSetting(
                short_name="ai",
                description="AI Ask Command",
                value="ai_enabled"
            ),
            FeatureSetting(
                short_name="factcheck",
                description="Fact Check",
                value="fact_check_enabled"
            ),
            FeatureSetting(
                short_name="grok",
                description="Grok AI",
                value="grok_enabled"
            ),
            FeatureSetting(
                short_name="qotd",
                description="Question of the Day",
                value="qotd_enabled"
            ),
        ]

    @cached_property
    def feature_map(self) -> dict[str, str]:
        """Return a mapping of feature short names to their database field names."""
        return {feature.short_name: feature.value for feature in self.features}

    @cached_property
    def feature_names(self) -> dict[str, str]:
        """Return a mapping of feature short names to their display names."""
        return {feature.short_name: feature.description for feature in self.features}

    @cached_property
    def available_features(self) -> list[str]:
        """Return a list of all available feature short names."""
        return [feature.short_name for feature in self.features]


