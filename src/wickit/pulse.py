"""pulse - Progress Tracking and Analytics.

Track streaks, retention, and learning progress with analytics.
Provides insights into user activity and performance.

Example:
    >>> from wickit import pulse
    >>> tracker = pulse.StreakTracker()
    >>> tracker.record_review(quality=4)
    >>> metrics = pulse.calculate_progress_metrics(tracker)
    >>> retention = pulse.get_retention_message(tracker)

Classes:
    StreakData: User streak information.
    StreakTracker: Tracks daily streaks.
    RetentionPoint: Single retention data point.
    RetentionAnalyzer: Analyzes retention over time.
    ProgressMetrics: Aggregated progress metrics.

Functions:
    calculate_progress_metrics: Get progress metrics.
    get_retention_message: Get retention summary.
    get_weak_spots: Identify weak areas.
    get_recommendations: Get study recommendations.
    generate_analytics_summary: Generate full summary.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional


@dataclass
class StreakData:
    """User streak information."""
    current_streak: int = 0
    longest_streak: int = 0
    last_active: Optional[str] = None
    total_days_active: int = 0


class StreakTracker:
    """Track user streaks and activity."""

    def __init__(self, data: StreakData = None):
        self.data = data or StreakData()

    def update(self, today: date = None) -> StreakData:
        """Update streak after activity."""
        today = today or date.today()
        today_str = today.isoformat()
        last_active = self.data.last_active

        if last_active != today_str:
            if last_active:
                last_date = date.fromisoformat(last_active)
                if (today - last_date).days == 1:
                    self.data.current_streak += 1
                else:
                    self.data.current_streak = 1

                if self.data.current_streak > self.data.longest_streak:
                    self.data.longest_streak = self.data.current_streak
            else:
                self.data.current_streak = 1

            self.data.last_active = today_str
            self.data.total_days_active += 1

        return self.data

    def get_message(self) -> str:
        """Get motivational message based on streak."""
        if self.data.current_streak == 0:
            return "Start your streak today! Every day counts."
        elif self.data.current_streak == 1:
            return "Great start! Keep it going tomorrow."
        elif self.data.current_streak < 7:
            return f"{self.data.current_streak} day streak! You're building a habit."
        elif self.data.current_streak < 30:
            return f"{self.data.current_streak} days! Making great progress."
        elif self.data.current_streak < 100:
            return f"{self.data.current_streak} day streak! Incredible dedication."
        else:
            return f"{self.data.current_streak} days! You're a legend."


@dataclass
class RetentionPoint:
    """Data point for retention curve."""
    day: int
    retention: float


class RetentionAnalyzer:
    """Analyze retention over time."""

    def __init__(self, reviews: list = None):
        self.reviews = reviews or []

    def add_review(self, card_id: str, quality: int, timestamp: datetime):
        """Record a review."""
        self.reviews.append({
            "card_id": card_id,
            "quality": quality,
            "timestamp": timestamp,
        })

    def get_retention_curve(self, days: int = 30) -> list:
        """Calculate retention curve over N days.

        Returns list of (day, avg_retention) points.
        """
        curve = []
        today = datetime.now().date()

        for day_offset in range(days):
            day = today - timedelta(days=day_offset)
            day_reviews = [r for r in self.reviews if r["timestamp"].date() <= day]

            if day_reviews:
                avg_quality = sum(r["quality"] for r in day_reviews) / len(day_reviews)
                retention = (avg_quality / 5.0) * 100
                curve.append(RetentionPoint(day=day_offset, retention=retention))
            else:
                curve.append(RetentionPoint(day=day_offset, retention=0.0))

        return curve

    def get_avg_retention(self, days: int = 7) -> float:
        """Get average retention over N days."""
        curve = self.get_retention_curve(days)
        non_zero = [p.retention for p in curve if p.retention > 0]
        return sum(non_zero) / len(non_zero) if non_zero else 0.0


@dataclass
class ProgressMetrics:
    """Overall progress metrics."""

    total_sessions: int = 0
    total_reviews: int = 0
    total_correct: int = 0
    total_incorrect: int = 0
    average_quality: float = 0.0
    time_spent_minutes: int = 0
    session_dates: set = field(default_factory=set)


def calculate_progress_metrics(sessions: list) -> ProgressMetrics:
    """Calculate progress from session data."""
    metrics = ProgressMetrics()

    for session in sessions:
        metrics.total_sessions += 1
        if session.get("date"):
            metrics.session_dates.add(session["date"][:10])

        questions = session.get("questions", [])
        metrics.total_reviews += len(questions)

        correct = sum(1 for q in questions if q.get("correct"))
        incorrect = sum(1 for q in questions if not q.get("correct"))
        metrics.total_correct += correct
        metrics.total_incorrect += incorrect

        total_quality = sum(q.get("quality", 0) for q in questions if q.get("quality") is not None)
        count_with_quality = sum(1 for q in questions if q.get("quality") is not None)
        if count_with_quality > 0:
            metrics.average_quality = total_quality / count_with_quality

    return metrics


def get_retention_message(avg_retention: float) -> str:
    """Get message based on retention rate."""
    if avg_retention >= 90:
        return "Excellent retention! You're mastering this."
    elif avg_retention >= 75:
        return "Good retention. Keep practicing to improve."
    elif avg_retention >= 50:
        return "Fair retention. Consider reviewing more often."
    elif avg_retention >= 25:
        return "Low retention. Increase review frequency."
    else:
        return "Very low retention. Focus on difficult cards."


def get_weak_spots(questions: list, threshold: float = 0.5) -> list:
    """Identify weak areas from question data.

    Args:
        questions: List of question dicts with 'question', 'correct', 'category'
        threshold: Ratio below which to flag as weak

    Returns:
        List of weak spot dicts with category and stats
    """
    categories = {}
    for q in questions:
        cat = q.get("category", "Uncategorized")
        if cat not in categories:
            categories[cat] = {"total": 0, "correct": 0}
        categories[cat]["total"] += 1
        if q.get("correct"):
            categories[cat]["correct"] += 1

    weak_spots = []
    for cat, stats in categories.items():
        ratio = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        if ratio < threshold:
            weak_spots.append({
                "category": cat,
                "accuracy": round(ratio * 100, 1),
                "total_questions": stats["total"],
                "correct_answers": stats["correct"],
            })

    return sorted(weak_spots, key=lambda x: x["accuracy"])


def get_recommendations(weak_spots: list, retention: float) -> list:
    """Generate recommendations based on analysis."""
    recommendations = []

    if retention < 50:
        recommendations.append({
            "type": "retention",
            "priority": "high",
            "message": "Your retention is low. Try reviewing for shorter periods but more frequently.",
        })

    for spot in weak_spots[:3]:
        recommendations.append({
            "type": "weak_spot",
            "priority": "medium",
            "message": f"Focus on '{spot['category']}' - only {spot['accuracy']}% accuracy.",
        })

    if not recommendations:
        recommendations.append({
            "type": "positive",
            "priority": "low",
            "message": "Great work! Keep up the consistent practice.",
        })

    return recommendations


@dataclass
class AnalyticsSummary:
    """Complete analytics summary."""
    streak: StreakData
    retention_curve: list
    average_retention: float
    retention_message: str
    weak_spots: list
    recommendations: list
    metrics: ProgressMetrics


def generate_analytics_summary(
    streak_data: StreakData,
    reviews: list,
    sessions: list,
    questions: list
) -> AnalyticsSummary:
    """Generate complete analytics summary."""
    tracker = StreakTracker(streak_data)
    tracker.update()

    analyzer = RetentionAnalyzer(reviews)
    retention_curve = analyzer.get_retention_curve()
    avg_retention = analyzer.get_avg_retention()

    metrics = calculate_progress_metrics(sessions)
    weak_spots = get_weak_spots(questions)
    recommendations = get_recommendations(weak_spots, avg_retention)

    return AnalyticsSummary(
        streak=tracker.data,
        retention_curve=[{"day": p.day, "retention": p.retention} for p in retention_curve],
        average_retention=avg_retention,
        retention_message=get_retention_message(avg_retention),
        weak_spots=weak_spots,
        recommendations=recommendations,
        metrics=metrics,
    )
