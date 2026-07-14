class RecoveryScoreEngine:
    """
    Computes ARWA's Recovery Score before and after
    the AI-generated recovery strategy.

    This becomes the headline metric shown to users
    and judges.
    """

    # ---------------------------------------------

    def calculate_current(
        self,
        state,
    ):

        academic = state.academic_risk.score

        burnout = state.burnout_risk.score

        score = (

            (1 - academic) * 60

            +

            (1 - burnout) * 40

        )

        return self._build_result(score)

    # ---------------------------------------------

    def calculate_projected(
        self,
        state,
        strategy,
    ):

        evaluation = strategy["evaluation"]

        academic = state.academic_risk.score

        burnout = state.burnout_risk.score

        score = (

            (1 - academic) * 40

            +

            (1 - burnout) * 20

            +

            evaluation["grade_gain"] * 4

            +

            evaluation["urgency_bonus"] * 2

            -

            evaluation["burnout"] * 10

            -

            evaluation["time_cost"]

        )

        return self._build_result(score)

    # ---------------------------------------------

    def calculate_improvement(
        self,
        current,
        projected,
    ):

        return {

            "before": current,

            "after": projected,

            "improvement":

                projected["score"]

                -

                current["score"]

        }

    # ---------------------------------------------

    def _build_result(
        self,
        score,
    ):

        score = max(
            0,
            min(
                round(score),
                100,
            ),
        )

        probability = score

        if score >= 85:
            status = "Excellent"

        elif score >= 70:
            status = "Good"

        elif score >= 50:
            status = "Recovering"

        elif score >= 30:
            status = "At Risk"

        else:
            status = "Critical"

        return {

            "score": score,

            "status": status,

            "probability": probability,

        }