"""synapse - Spaced Repetition (SM-2).

Implementation of the SM-2 spaced repetition algorithm for learning and
memory optimization. Calculates optimal review intervals based on performance.

The algorithm adjusts intervals based on:
- Quality rating (0-5) of your recall
- Previous interval length
- Ease factor (difficulty multiplier)
- Number of successful repetitions

Example:
    >>> from wickit import synapse
    >>> card = synapse.SM2Card(front="What is Python?", back="A programming language")
    >>> synapse.review_card(card, quality=5)  # quality: 0-5
    >>> interval = synapse.calculate_interval(card)
    >>> is_due = synapse.is_due(card)

Classes:
    SM2Card: Flashcard with SM-2 scheduling data.
    Deck: Collection of cards.

Functions:
    review_card: Review a card and update scheduling.
    calculate_interval: Calculate next review interval.
    is_due: Check if card needs review.
    get_retention_score: Get calculated retention percentage.
    ease_factor_for_quality: Calculate ease factor from quality.
    get_grade_label: Get human-readable grade label.

Constants:
    DEFAULT_EASE_FACTOR = 2.5
    MIN_EASE_FACTOR = 1.3
    MAX_EASE_FACTOR = 3.0
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
MAX_EASE_FACTOR = 3.0


@dataclass
class SM2Card:
    """Single flashcard with SM-2 scheduling data.

    Attributes:
        id: Unique identifier for the card
        front: Question or prompt side
        back: Answer side
        tags: Optional tags for categorization
        ease_factor: Difficulty multiplier (1.3-3.0), 2.5 is default
        interval: Days until next review
        repetitions: Number of successful reviews
        next_review: Date for next review (defaults to today)
        created_at: ISO timestamp when created
        last_reviewed: ISO timestamp of last review
    """
    id: str
    front: str
    back: str
    tags: list = field(default_factory=list)
    ease_factor: float = DEFAULT_EASE_FACTOR
    interval: int = 0
    repetitions: int = 0
    next_review: Optional[date] = None
    created_at: Optional[str] = None
    last_reviewed: Optional[str] = None

    def __post_init__(self):
        if self.next_review is None:
            self.next_review = date.today()
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Serialize card to dictionary."""
        return {
            "id": self.id,
            "front": self.front,
            "back": self.back,
            "tags": self.tags,
            "ease_factor": self.ease_factor,
            "interval": self.interval,
            "repetitions": self.repetitions,
            "next_review": self.next_review.isoformat() if isinstance(self.next_review, date) else self.next_review,
            "created_at": self.created_at,
            "last_reviewed": self.last_reviewed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SM2Card":
        """Deserialize card from dictionary."""
        next_review = data.get("next_review")
        if next_review and isinstance(next_review, str):
            next_review = date.fromisoformat(next_review)
        return cls(
            id=data["id"],
            front=data["front"],
            back=data["back"],
            tags=data.get("tags", []),
            ease_factor=data.get("ease_factor", DEFAULT_EASE_FACTOR),
            interval=data.get("interval", 0),
            repetitions=data.get("repetitions", 0),
            next_review=next_review,
            created_at=data.get("created_at"),
            last_reviewed=data.get("last_reviewed"),
        )


def calculate_interval(card: SM2Card, quality: int) -> tuple[int, float]:
    """Calculate next review interval using SM-2 algorithm.

    Args:
        card: The card being reviewed
        quality: Rating 0-5:
            0 - Complete blackout, wrong response
            1 - Incorrect, but easy to recall once seen
            2 - Incorrect, but remembered after seeing answer
            3 - Correct with serious difficulty
            4 - Correct after hesitation
            5 - Perfect response

    Returns:
        Tuple of (new_interval_days, new_ease_factor)
    """
    quality = max(0, min(5, quality))

    new_ef = card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(MIN_EASE_FACTOR, min(MAX_EASE_FACTOR, new_ef))

    if quality < 3:
        new_interval = 1
        repetitions = 0
    else:
        if card.repetitions == 0:
            new_interval = 1
        elif card.repetitions == 1:
            new_interval = 6
        else:
            new_interval = int(card.interval * new_ef)
        repetitions = card.repetitions + 1

    return new_interval, new_ef


def review_card(card: SM2Card, quality: int) -> SM2Card:
    """Review a card and update its scheduling data.

    Args:
        card: The card being reviewed
        quality: Rating 0-5 (see calculate_interval)

    Returns:
        Updated card with new interval and ease factor
    """
    new_interval, new_ef = calculate_interval(card, quality)

    card.ease_factor = new_ef
    card.interval = new_interval

    if quality >= 3:
        card.repetitions += 1
    else:
        card.repetitions = 0

    card.next_review = date.today() + new_interval
    card.last_reviewed = datetime.now().isoformat()

    return card


def ease_factor_for_quality(quality: int, current_ef: float = DEFAULT_EASE_FACTOR) -> float:
    """Calculate new ease factor for a quality rating.

    Args:
        quality: Rating 0-5
        current_ef: Current ease factor (default 2.5)

    Returns:
        New ease factor
    """
    new_ef = current_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return max(MIN_EASE_FACTOR, min(MAX_EASE_FACTOR, new_ef))


def get_grade_label(quality: int) -> str:
    """Get human-readable label for quality rating.

    Args:
        quality: Rating 0-5

    Returns:
        Label string
    """
    labels = {
        0: "Blackout",
        1: "Failed (Easy)",
        2: "Failed (Remembered)",
        3: "Hard",
        4: "Good",
        5: "Perfect",
    }
    return labels.get(quality, "Unknown")


def is_due(card: SM2Card, today: date = None) -> bool:
    """Check if a card is due for review.

    Args:
        card: The card to check
        today: Reference date (defaults to today)

    Returns:
        True if card is due
    """
    today = today or date.today()
    return card.next_review <= today


def get_retention_score(card: SM2Card) -> float:
    """Calculate estimated retention score for a card.

    Args:
        card: The card to score

    Returns:
        Score 0-100 representing estimated retention probability
    """
    if card.repetitions == 0:
        return 0.0

    base_retention = 0.85
    bonus = min(0.14, card.repetitions * 0.02)
    ef_bonus = min(0.1, (card.ease_factor - MIN_EASE_FACTOR) * 0.05)

    return min(100.0, (base_retention + bonus + ef_bonus) * 100)


@dataclass
class Deck:
    """Collection of SM-2 cards."""

    id: str
    name: str
    description: str = ""
    cards: list = field(default_factory=list)
    created_at: Optional[str] = None
    source: str = "manual"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.cards = [SM2Card.from_dict(c) if isinstance(c, dict) else c for c in self.cards]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "cards": [c.to_dict() for c in self.cards],
            "created_at": self.created_at,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Deck":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            cards=data.get("cards", []),
            created_at=data.get("created_at"),
            source=data.get("source", "manual"),
        )

    def get_due_cards(self, today: date = None) -> list:
        """Get cards due for review."""
        today = today or date.today()
        return [c for c in self.cards if is_due(c, today)]

    def get_new_cards(self) -> list:
        """Get cards never reviewed."""
        return [c for c in self.cards if c.repetitions == 0]

    def get_reviewed_today(self, today: date = None) -> int:
        """Count cards reviewed today."""
        today = today or date.today()
        return sum(1 for c in self.cards if c.last_reviewed and c.last_reviewed.startswith(today.isoformat()))
