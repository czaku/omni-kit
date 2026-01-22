"""landscape - Platform Detection and Categorization.

Detect and categorize platforms/URLs for routing or classification.
Supports predefined platforms and custom registration.

Example:
    >>> from wickit import landscape
    >>> platform = landscape.detect_platform("https://github.com/user/repo")
    >>> categories = landscape.list_platforms_by_category(landscape.PlatformCategory.CODE)

Classes:
    Platform: Platform definition with name, domains, category.
    PlatformCategory: Enum (CODE, SOCIAL, PRODUCTIVITY, MEDIA, NEWS, SHOPPING, OTHER).

Functions:
    detect_platform: Detect platform from URL.
    get_platform: Get platform by name.
    list_platforms: List all platforms.
    list_platforms_by_category: List platforms in category.
    categorize_url: Get category for URL.
    register_platform: Add custom platform.
    unregister_platform: Remove platform.
    get_all_categories: List all categories.

Predefined Platforms:
    GitHub, GitLab, Bitbucket (CODE)
    Twitter, LinkedIn, Reddit (SOCIAL)
    Notion, Slack, Trello (PRODUCTIVITY)
    YouTube, Spotify (MEDIA)
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PlatformCategory(Enum):
    """Categories for platform types."""
    LMS = "lms"
    JOB_BOARD = "job_board"
    VIDEO = "video"
    SOCIAL = "social"
    CHAT = "chat"
    QUIZ = "quiz"
    LEARNING = "learning"
    CUSTOM = "custom"


@dataclass
class Platform:
    """Platform metadata."""
    id: str
    name: str
    category: PlatformCategory
    url_patterns: list
    features: list = None
    description: str = ""


# Predefined platforms
PLATFORMS = {
    # LMS Platforms
    "canvas": Platform(
        id="canvas",
        name="Canvas",
        category=PlatformCategory.LMS,
        url_patterns=[
            r"canvas\.edu",
            r"canvas\.ucsf\.edu",
            r"canvas\.harvard\.edu",
        ],
        features=["quizzes", "assignments", "discussions"],
        description="Instructure Canvas LMS",
    ),
    "blackboard": Platform(
        id="blackboard",
        name="Blackboard",
        category=PlatformCategory.LMS,
        url_patterns=[
            r"blackboard\.com",
            r"bb\.csulb\.edu",
        ],
        features=["quizzes", "assignments"],
        description="Blackboard Learn",
    ),
    "moodle": Platform(
        id="moodle",
        name="Moodle",
        category=PlatformCategory.LMS,
        url_patterns=[
            r"moodle\.org",
            r"moodle\.com",
            r"/moodle/",
        ],
        features=["quizzes", "forums", "assignments"],
        description="Open-source Moodle LMS",
    ),
    "d2l": Platform(
        id="d2l",
        name="Brightspace/D2L",
        category=PlatformCategory.LMS,
        url_patterns=[
            r"brightspace\.com",
            r"d2l\.bcit\.ca",
        ],
        features=["quizzes", "content"],
        description="D2L Brightspace",
    ),
    "schoology": Platform(
        id="schoology",
        name="Schoology",
        category=PlatformCategory.LMS,
        url_patterns=[
            r"schoology\.com",
        ],
        features=["quizzes", "assignments"],
        description="Schoology LMS",
    ),

    # Job Boards
    "linkedin": Platform(
        id="linkedin",
        name="LinkedIn",
        category=PlatformCategory.JOB_BOARD,
        url_patterns=[
            r"linkedin\.com",
        ],
        features=["jobs", "profile", "networking"],
        description="LinkedIn Job Board",
    ),
    "indeed": Platform(
        id="indeed",
        name="Indeed",
        category=PlatformCategory.JOB_BOARD,
        url_patterns=[
            r"indeed\.com",
        ],
        features=["job_search", "applications"],
        description="Indeed Job Board",
    ),
    "glassdoor": Platform(
        id="glassdoor",
        name="Glassdoor",
        category=PlatformCategory.JOB_BOARD,
        url_patterns=[
            r"glassdoor\.com",
        ],
        features=["job_search", "reviews"],
        description="Glassdoor Job Board",
    ),
    "ziprecruiter": Platform(
        id="ziprecruiter",
        name="ZipRecruiter",
        category=PlatformCategory.JOB_BOARD,
        url_patterns=[
            r"ziprecruiter\.com",
        ],
        features=["job_search", "applications"],
        description="ZipRecruiter",
    ),
    "monster": Platform(
        id="monster",
        name="Monster",
        category=PlatformCategory.JOB_BOARD,
        url_patterns=[
            r"monster\.com",
        ],
        features=["job_search"],
        description="Monster Job Board",
    ),

    # Quiz Platforms
    "quizlet": Platform(
        id="quizlet",
        name="Quizlet",
        category=PlatformCategory.QUIZ,
        url_patterns=[
            r"quizlet\.com",
        ],
        features=["flashcards", "quizzes", "study_sets"],
        description="Quizlet Study Platform",
    ),
    "kahoot": Platform(
        id="kahoot",
        name="Kahoot!",
        category=PlatformCategory.QUIZ,
        url_patterns=[
            r"kahoot\.com",
        ],
        features=["games", "quizzes"],
        description="Kahoot Game-Based Learning",
    ),
    "proprofs": Platform(
        id="proprofs",
        name="ProProfs",
        category=PlatformCategory.QUIZ,
        url_patterns=[
            r"proprofs\.com",
        ],
        features=["quizzes", "tests"],
        description="ProProfs Quiz Maker",
    ),

    # Google Forms (often used for quizzes)
    "google_forms": Platform(
        id="google_forms",
        name="Google Forms",
        category=PlatformCategory.QUIZ,
        url_patterns=[
            r"docs\.google\.com/forms",
        ],
        features=["forms", "quizzes"],
        description="Google Forms for Quizzes",
    ),

    # Video Platforms
    "youtube": Platform(
        id="youtube",
        name="YouTube",
        category=PlatformCategory.VIDEO,
        url_patterns=[
            r"youtube\.com",
            r"youtu\.be",
        ],
        features=["videos", "playlists"],
        description="YouTube",
    ),
    "vimeo": Platform(
        id="vimeo",
        name="Vimeo",
        category=PlatformCategory.VIDEO,
        url_patterns=[
            r"vimeo\.com",
        ],
        features=["videos"],
        description="Vimeo",
    ),

    # Social
    "facebook": Platform(
        id="facebook",
        name="Facebook",
        category=PlatformCategory.SOCIAL,
        url_patterns=[
            r"facebook\.com",
            r"fb\.com",
        ],
        features=["posts", "groups"],
        description="Facebook",
    ),
    "twitter": Platform(
        id="twitter",
        name="X (Twitter)",
        category=PlatformCategory.SOCIAL,
        url_patterns=[
            r"twitter\.com",
            r"x\.com",
        ],
        features=["posts", "feed"],
        description="X (formerly Twitter)",
    ),
    "reddit": Platform(
        id="reddit",
        name="Reddit",
        category=PlatformCategory.SOCIAL,
        url_patterns=[
            r"reddit\.com",
        ],
        features=["posts", "comments"],
        description="Reddit",
    ),

    # Chat
    "slack": Platform(
        id="slack",
        name="Slack",
        category=PlatformCategory.CHAT,
        url_patterns=[
            r"slack\.com",
        ],
        features=["messages", "channels"],
        description="Slack",
    ),
    "discord": Platform(
        id="discord",
        name="Discord",
        category=PlatformCategory.CHAT,
        url_patterns=[
            r"discord\.com",
            r"discord\.gg",
        ],
        features=["messages", "servers"],
        description="Discord",
    ),
}


def detect_platform(url: str) -> Optional[Platform]:
    """Detect platform from URL.

    Args:
        url: The URL to check

    Returns:
        Platform if detected, None otherwise
    """
    for platform in PLATFORMS.values():
        for pattern in platform.url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return None


def get_platform(platform_id: str) -> Optional[Platform]:
    """Get platform by ID.

    Args:
        platform_id: The platform identifier

    Returns:
        Platform if found, None otherwise
    """
    return PLATFORMS.get(platform_id)


def get_platforms_by_category(category: PlatformCategory) -> list:
    """Get all platforms in a category."""
    return [p for p in PLATFORMS.values() if p.category == category]


def get_platform_info(platform_id: str) -> dict:
    """Get formatted platform information."""
    platform = get_platform(platform_id)
    if not platform:
        return {"error": f"Unknown platform: {platform_id}"}

    return {
        "id": platform.id,
        "name": platform.name,
        "category": platform.category.value,
        "features": platform.features,
        "description": platform.description,
    }


def list_platforms() -> list:
    """List all registered platforms."""
    return [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category.value,
        }
        for p in PLATFORMS.values()
    ]


def list_platforms_by_category(category: str) -> list:
    """List platforms filtered by category."""
    try:
        cat = PlatformCategory(category)
    except ValueError:
        return []

    return [
        {"id": p.id, "name": p.name}
        for p in PLATFORMS.values()
        if p.category == cat
    ]


def register_platform(platform: Platform) -> None:
    """Register a new platform.

    Args:
        platform: Platform to register
    """
    PLATFORMS[platform.id] = platform


def unregister_platform(platform_id: str) -> bool:
    """Unregister a platform.

    Args:
        platform_id: ID of platform to remove

    Returns:
        True if removed, False if not found
    """
    if platform_id in PLATFORMS:
        del PLATFORMS[platform_id]
        return True
    return False


def categorize_url(url: str) -> str:
    """Get category for a URL.

    Args:
        url: The URL to categorize

    Returns:
        Category name or "unknown"
    """
    platform = detect_platform(url)
    if platform:
        return platform.category.value
    return "unknown"


def get_all_categories() -> list:
    """Get all available categories."""
    return [cat.value for cat in PlatformCategory]
