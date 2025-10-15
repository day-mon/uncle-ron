from pydantic import BaseModel, Field
from enum import Enum


class PollType(str, Enum):
    """Types of polls."""

    CONTROVERSIAL = "controversial"
    DEBATE = "debate"
    OPINION = "opinion"
    CURRENT_EVENTS = "current_events"
    SOCIAL_ISSUE = "social_issue"


class QOTDResponse(BaseModel):
    """Response model for QOTD generation."""

    question: str = Field(description="The controversial thought-provoking question")
    poll_type: PollType = Field(description="The type of poll being generated")
    option_a: str = Field(description="Option A - first viewpoint")
    option_b: str = Field(description="Option B - second viewpoint")
    option_c: str = Field(description="Option C - third viewpoint")
    option_d: str = Field(description="Option D - fourth viewpoint")
    reasoning: str = Field(
        description="Brief explanation of why this question is thought-provoking"
    )
    expected_discussion: str = Field(
        description="What kind of discussion this question should spark"
    )

    @property
    def options(self):
        return [self.option_a, self.option_b, self.option_c, self.option_d]

    def get_emoji_options(self) -> list[str]:
        """Get options with emoji prefixes."""
        emojis = ["🇦", "🇧", "🇨", "🇩"]
        return [f"{emojis[i]} {option}" for i, option in enumerate(self.options)]
