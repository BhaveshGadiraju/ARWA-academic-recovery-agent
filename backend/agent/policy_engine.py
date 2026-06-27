from models.state_vector import StudentState


class PolicyDecision:
    """
    Final action chosen for a task after applying
    ARWA's academic recovery policies.
    """

    def __init__(
        self,
        action: str,
        reason: str,
        confidence: float,
    ):
        self.action = action
        self.reason = reason
        self.confidence = confidence


class PolicyEngine:
    """
    Applies academic recovery policies to
    scored tasks produced by the DecisionEngine.
    """

    def evaluate(
        self,
        task: dict,
        score: float,
        state: StudentState,
    ) -> PolicyDecision:

        academic = state.academic_risk.score
        burnout = state.burnout_risk.score

        due = task["due_in_hours"]
        difficulty = task["difficulty"]
        points = task["points_value"]

        # --------------------------
        # Emergency Policy
        # --------------------------

        if due <= 6:

            return PolicyDecision(
                action="DO",
                reason="Critical deadline approaching.",
                confidence=0.99,
            )

        # --------------------------
        # Burnout Protection
        # --------------------------

        if burnout >= 0.80 and difficulty >= 8:

            return PolicyDecision(
                action="DELAY",
                reason="High burnout risk detected.",
                confidence=0.92,
            )

        # --------------------------
        # Low Value Work
        # --------------------------

        if points <= 5 and due > 48:

            return PolicyDecision(
                action="DROP",
                reason="Low academic impact.",
                confidence=0.90,
            )

        # --------------------------
        # Academic Recovery
        # --------------------------

        if academic >= 0.70 and score >= 7:

            return PolicyDecision(
                action="DO",
                reason="High academic recovery value.",
                confidence=0.88,
            )

        # --------------------------
        # Score Threshold
        # --------------------------

        if score >= 8:

            return PolicyDecision(
                action="DO",
                reason="High priority task.",
                confidence=0.85,
            )

        return PolicyDecision(
            action="DELAY",
            reason="Lower priority than other work.",
            confidence=0.75,
        )