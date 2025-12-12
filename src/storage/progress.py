"""Progress tracking utilities."""

from datetime import datetime, timedelta
from typing import Optional

from .database import Database


class ProgressTracker:
    """Track and analyze user's learning progress."""

    def __init__(self, db: Database):
        """Initialize the progress tracker.

        Args:
            db: Database instance
        """
        self.db = db

    async def get_summary(self) -> dict:
        """Get a summary of user's progress.

        Returns:
            Dict with progress metrics
        """
        progress = await self.db.get_overall_progress()
        completed = await self.db.get_completed_challenges()
        keybinds = await self.db.get_learned_keybinds()

        # Calculate streak (days in a row with activity)
        streak = await self._calculate_streak()

        # Get most practiced keybinds
        stats = await self.db.get_practice_stats()
        most_practiced = sorted(
            stats.items(),
            key=lambda x: x[1]["total_attempts"],
            reverse=True,
        )[:5]

        return {
            "challenges_completed": progress["completed_challenges"],
            "keybinds_learned": progress["learned_keybinds"],
            "keybinds_integrated": progress["integrated_keybinds"],
            "total_practice": progress["total_practice_sessions"],
            "current_streak": streak,
            "recent_completions": completed[:5],
            "recent_keybinds": keybinds[:5],
            "most_practiced": [
                {"keybind": k, **v} for k, v in most_practiced
            ],
        }

    async def _calculate_streak(self) -> int:
        """Calculate the current streak of consecutive practice days."""
        # This is a simplified implementation
        # A full implementation would query practice_history by date
        async with self.db.connection.execute(
            """
            SELECT DISTINCT DATE(practiced_at) as practice_date
            FROM practice_history
            ORDER BY practice_date DESC
            LIMIT 30
            """
        ) as cursor:
            rows = await cursor.fetchall()

        if not rows:
            return 0

        dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in rows]
        today = datetime.now().date()

        # Check if practiced today or yesterday
        if dates[0] < today - timedelta(days=1):
            return 0

        streak = 1
        for i in range(1, len(dates)):
            if dates[i] == dates[i - 1] - timedelta(days=1):
                streak += 1
            else:
                break

        return streak

    async def get_recommendations(self) -> list[dict]:
        """Get personalized recommendations for what to learn next.

        Returns:
            List of recommended keybinds/challenges
        """
        recommendations = []

        # Get completed challenges
        completed = await self.db.get_completed_challenges()
        completed_ids = {c["challenge_id"] for c in completed}

        # Get practice stats
        stats = await self.db.get_practice_stats()

        # Recommend keybinds with low success rate for more practice
        for keybind, data in stats.items():
            if data["success_rate"] < 0.8 and data["total_attempts"] >= 3:
                recommendations.append({
                    "type": "practice",
                    "keybind": keybind,
                    "reason": f"Success rate is {data['success_rate']:.0%} - more practice recommended",
                })

        # Recommend challenges not yet completed
        from ..challenges.types import BUILTIN_CHALLENGES

        for challenge in BUILTIN_CHALLENGES:
            if challenge.id not in completed_ids:
                recommendations.append({
                    "type": "challenge",
                    "challenge_id": challenge.id,
                    "name": challenge.name,
                    "difficulty": challenge.difficulty,
                    "reason": "Challenge not yet completed",
                })
                if len(recommendations) >= 5:
                    break

        return recommendations

    async def log_challenge_complete(
        self,
        challenge_id: str,
        time_taken: float,
        attempts: int,
    ) -> None:
        """Log completion of a challenge.

        Args:
            challenge_id: ID of completed challenge
            time_taken: Time in seconds
            attempts: Number of attempts
        """
        await self.db.mark_challenge_completed(challenge_id, time_taken, attempts)

    async def log_keybind_learned(
        self,
        keybind: str,
        command: str,
        description: Optional[str] = None,
    ) -> None:
        """Log that a keybind was learned.

        Args:
            keybind: The keybind (e.g., "M-h")
            command: The tmux command
            description: Optional description
        """
        await self.db.add_learned_keybind(keybind, command, description)

    async def log_practice(self, keybind: str, success: bool = True) -> None:
        """Log a practice attempt.

        Args:
            keybind: The keybind practiced
            success: Whether it was successful
        """
        await self.db.log_practice(keybind, success)
