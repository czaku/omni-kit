"""humanize - Human-Like Mistake Injection.

Inject realistic mistakes into text for training data augmentation,
testing, or simulating human behavior.

Example:
    >>> from wickit import humanize
    >>> mistaker = humanize.Mistaker(level=humanize.MISTAKE_LEVELS["medium"])
    >>> if humanize.should_make_mistakes():
    ...     result = mistaker.inject_mistakes(text)

Classes:
    Mistaker: Mistake injection engine.
    MistakeConfig: Configuration for mistakes.

Functions:
    Mistaker.inject_mistakes: Add mistakes to text.
    should_make_mistakes: Check if mistakes enabled.
    set_mistake_level: Set mistake frequency.
    record_answer: Record answer pair.
    calculate_actual_score: Calculate with penalties.
    get_mistake_warning: Get warning message.

Mistake Levels:
    NONE, LOW, MEDIUM, HIGH, EXTREME
"""

import random
from dataclasses import dataclass
from typing import Optional


MISTAKE_LEVELS = {
    "none": {"rate": 0.0, "label": "Perfect", "score": "100%"},
    "slight": {"rate": 0.014, "label": "Human-like", "score": "~98.6%"},
    "moderate": {"rate": 0.03, "label": "Careless", "score": "~97%"},
    "grand": {"rate": 0.05, "label": "Sloppy", "score": "~95%"},
    "major": {"rate": 0.10, "label": "Struggling", "score": "~90%"},
}

DEFAULT_MISTAKE_LEVEL = "slight"


@dataclass
class MistakeConfig:
    """Configuration for mistake injection."""
    level: str = DEFAULT_MISTAKE_LEVEL
    rate: float = MISTAKE_LEVELS[DEFAULT_MISTAKE_LEVEL]["rate"]


class Mistaker:
    """Inject human-like mistakes into text or answers."""

    def __init__(self, level: str = DEFAULT_MISTAKE_LEVEL):
        self.level = level
        self.rate = MISTAKE_LEVELS[level]["rate"]

    def should_mistake(self) -> bool:
        """Determine if a mistake should be made."""
        if self.rate == 0.0:
            return False
        return random.random() < self.rate

    def inject_typo(self, text: str) -> str:
        """Inject a realistic typo."""
        if len(text) < 2:
            return text

        typo_types = [
            self._swap_adjacent,
            self._delete_character,
            self._duplicate_character,
            self._substitute_character,
        ]

        typo_func = random.choice(typo_types)
        position = random.randint(0, len(text) - 2)
        return typo_func(text, position)

    def _swap_adjacent(self, text: str, position: int) -> str:
        """Swap two adjacent characters."""
        chars = list(text)
        chars[position], chars[position + 1] = chars[position + 1], chars[position]
        return "".join(chars)

    def _delete_character(self, text: str, position: int) -> str:
        """Delete a character."""
        return text[:position] + text[position + 1:]

    def _duplicate_character(self, text: str, position: int) -> str:
        """Duplicate a character."""
        return text[:position + 1] + text[position] + text[position + 1:]

    def _substitute_character(self, text: str, position: int) -> str:
        """Substitute a character with a nearby key."""
        nearby = {
            "a": "sq", "b": "vn", "c": "xv", "d": "sf",
            "e": "wr", "f": "dg", "g": "fh", "h": "gj",
            "i": "uo", "j": "hk", "k": "jl", "l": "ko",
            "m": "n", "n": "bm", "o": "ip", "p": "ol",
            "q": "wa", "r": "et", "s": "ad", "t": "ry",
            "u": "yi", "v": "cb", "w": "qe", "x": "zc",
            "y": "tu", "z": "sx",
        }
        char = text[position].lower()
        if char in nearby:
            replacement = random.choice(nearby[char])
            return text[:position] + replacement + text[position + 1:]
        return text

    def inject_omission(self, text: str) -> str:
        """Omit a word or phrase."""
        words = text.split()
        if len(words) < 3:
            return text

        omit_count = random.randint(1, max(1, len(words) // 5))
        indices = random.sample(range(len(words)), omit_count)
        result = [w for i, w in enumerate(words) if i not in indices]
        return " ".join(result)

    def inject_word_substitution(self, text: str) -> str:
        """Substitute a word with a similar one."""
        substitutions = {
            "their": "there",
            "your": "you're",
            "its": "it's",
            "affect": "effect",
            "principal": "principle",
            "complement": "compliment",
            "definite": "definitive",
            "fewer": "less",
        }
        words = text.split()
        for i, word in enumerate(words):
            lower = word.lower().rstrip(".,!?")
            if lower in substitutions and random.random() < 0.3:
                replacement = substitutions[lower]
                if word[0].isupper():
                    replacement = replacement.capitalize()
                words[i] = word.replace(lower, replacement, 1)
                break
        return " ".join(words)

    def make_mistake(self, text: str, mistake_type: str = "auto") -> str:
        """Inject a mistake into text.

        Args:
            text: The text to modify
            mistake_type: Type of mistake (typo, omission, substitution, auto)

        Returns:
            Modified text with mistake
        """
        if mistake_type == "auto":
            types = ["typo", "typo", "omission", "substitution"]
            mistake_type = random.choice(types)

        if mistake_type == "typo":
            return self.inject_typo(text)
        elif mistake_type == "omission":
            return self.inject_omission(text)
        elif mistake_type == "substitution":
            return self.inject_word_substitution(text)
        else:
            return text

    def process_answer(self, correct_answer: str) -> tuple[str, bool]:
        """Process an answer, possibly with mistakes.

        Returns:
            Tuple of (processed_answer, made_mistake)
        """
        if not self.should_mistake():
            return correct_answer, False

        return self.make_mistake(correct_answer), True


def should_make_mistake(level: str = DEFAULT_MISTAKE_LEVEL) -> bool:
    """Determine if a mistake should be made based on level."""
    rate = MISTAKE_LEVELS[level]["rate"]
    if rate == 0.0:
        return False
    return random.random() < rate


def get_mistake_info(level: str) -> dict:
    """Get information about a mistake level."""
    if level not in MISTAKE_LEVELS:
        raise ValueError(f"Unknown mistake level: {level}")
    return MISTAKE_LEVELS[level]


def get_mistake_warning(level: str) -> str:
    """Get a warning message for a mistake level."""
    warnings = {
        "none": "Perfect accuracy - no mistakes expected",
        "slight": "Slight imperfections - 1.4% mistake rate",
        "moderate": "Moderate mistakes - 3% mistake rate",
        "grand": "Frequent mistakes - 5% mistake rate",
        "major": "Many mistakes - 10% mistake rate",
    }
    return warnings.get(level, "Unknown mistake level")


def set_mistake_level(level: str) -> Mistaker:
    """Create a Mistaker with the specified level."""
    if level not in MISTAKE_LEVELS:
        raise ValueError(f"Unknown mistake level: {level}")
    return Mistaker(level=level)


def record_answer(
    correct: bool,
    mistake_made: bool,
    level: str = DEFAULT_MISTAKE_LEVEL
) -> dict:
    """Record the result of answering with mistake injection."""
    return {
        "correct": correct,
        "mistake_made": mistake_made,
        "level": level,
        "timestamp": None,
    }


def calculate_actual_score(recorded_answers: list, level: str) -> float:
    """Calculate actual score accounting for mistake level."""
    if not recorded_answers:
        return 100.0

    total = len(recorded_answers)
    mistakes_expected = int(total * MISTAKE_LEVELS[level]["rate"])
    actual_mistakes = sum(1 for a in recorded_answers if a.get("mistake_made"))

    adjusted_mistakes = max(0, actual_mistakes - mistakes_expected)
    return 100.0 - (adjusted_mistakes / total * 100)
