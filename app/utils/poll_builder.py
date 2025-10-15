"""
Poll builder utility for creating Discord polls with common patterns.
"""

from datetime import timedelta
from discord import Poll, PollAnswer, PartialEmoji, Emoji


class PollBuilder:
    """Builder class for creating Discord polls with common patterns."""

    def __init__(self, question: str, duration: timedelta):
        self._poll = Poll(question=question, duration=duration)
        self._answers: list[PollAnswer] = []

    def add_answer(
        self, text: str, emoji: PartialEmoji | Emoji | str | None = None
    ) -> "PollBuilder":
        """Add an answer to the poll."""
        self._poll.add_answer(text=text, emoji=emoji)
        return self

    def add_answers(
        self,
        answers: list[str],
        emojis: list[PartialEmoji | Emoji | str] | None = None,
    ) -> "PollBuilder":
        """Add multiple answers to the poll."""
        for i, answer in enumerate(answers):
            emoji = emojis[i] if emojis and i < len(emojis) else None
            self._poll.add_answer(text=answer, emoji=emoji)
        return self

    def build(self) -> Poll:
        """Build and return the poll."""
        return self._poll

    @classmethod
    def simple_poll(
        cls, question: str, answers: list[str], duration_hours: int = 24
    ) -> "PollBuilder":
        """Create a simple poll with text answers."""
        return cls(
            question=question, duration=timedelta(hours=duration_hours)
        ).add_answers(answers)

    @classmethod
    def emoji_poll(
        cls,
        question: str,
        answers: list[str],
        emojis: list[str],
        duration_hours: int = 24,
    ) -> "PollBuilder":
        """Create a poll with emoji answers."""
        return cls(
            question=question, duration=timedelta(hours=duration_hours)
        ).add_answers(answers, emojis)

    @classmethod
    def yes_no_poll(cls, question: str, duration_hours: int = 24) -> "PollBuilder":
        """Create a simple yes/no poll."""
        return cls(
            question=question, duration=timedelta(hours=duration_hours)
        ).add_answers(["Yes", "No"], ["✅", "❌"])

    @classmethod
    def rating_poll(
        cls, question: str, max_rating: int = 5, duration_hours: int = 24
    ) -> "PollBuilder":
        """Create a rating poll (1 to max_rating)."""
        answers = [str(i) for i in range(1, max_rating + 1)]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][:max_rating]
        return cls(
            question=question, duration=timedelta(hours=duration_hours)
        ).add_answers(answers, emojis)
