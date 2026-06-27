from typing import List, Dict, Any
from datetime import datetime


class ExperienceRecord:
    """
    One historical record of ARWA's interaction.
    """

    def __init__(self, state_snapshot, plan, outcome_metrics):

        self.timestamp = datetime.now()

        self.state_snapshot = state_snapshot

        self.plan = plan

        self.outcome_metrics = outcome_metrics


class ExperienceMemory:
    """
    Stores historical student interactions so ARWA can learn patterns.
    """

    def __init__(self):

        self.history: List[ExperienceRecord] = []

    # -------------------------
    # STORE EXPERIENCE
    # -------------------------
    def store(self, state, plan, outcome_metrics: Dict):

        record = ExperienceRecord(
            state_snapshot=state,
            plan=plan,
            outcome_metrics=outcome_metrics
        )

        self.history.append(record)

    # -------------------------
    # PATTERN ANALYSIS
    # -------------------------
    def get_recent_patterns(self, limit=5):

        recent = self.history[-limit:]

        return [
            {
                "timestamp": r.timestamp,
                "academic_risk": r.state_snapshot.academic_risk.score,
                "burnout_risk": r.state_snapshot.burnout_risk.score,
                "completion_rate": r.outcome_metrics.get("completion_rate", 0),
                "avg_study_time": r.outcome_metrics.get("avg_study_time", 0),
            }
            for r in recent
        ]

    # -------------------------
    # SIMPLE INSIGHT ENGINE
    # -------------------------
    def generate_insights(self):

        if len(self.history) < 2:
            return ["Not enough history to generate insights."]

        insights = []

        latest = self.history[-1]

        prev = self.history[-2]

        # burnout trend
        if latest.state_snapshot.burnout_risk.score > prev.state_snapshot.burnout_risk.score:
            insights.append(
                "Burnout risk is increasing compared to previous session."
            )

        # academic risk trend
        if latest.state_snapshot.academic_risk.score > prev.state_snapshot.academic_risk.score:
            insights.append(
                "Academic risk is increasing — workload may be too high."
            )

        # completion insight
        if latest.outcome_metrics.get("completion_rate", 1) < 0.7:
            insights.append(
                "Low completion rate detected — schedule may be too aggressive."
            )

        if not insights:
            insights.append("Student performance is stable.")

        return insights