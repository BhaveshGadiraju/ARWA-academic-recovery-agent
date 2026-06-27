from models.state_vector import StudentState


class ReasoningEngine:
    """
    Generates evidence-based reasoning from the outputs
    of all AI modules.
    """

    def generate_reasoning(
        self,
        state: StudentState,
        decisions,
    ):

        if not decisions:
            return [
                "No academic tasks were provided."
            ]

        reasoning = []

        reasoning.extend(
            self._academic_reasoning(state)
        )

        reasoning.extend(
            self._burnout_reasoning(state)
        )

        reasoning.extend(
            self._decision_reasoning(decisions)
        )

        reasoning.append(
            self._overall_strategy(state, decisions)
        )

        return reasoning

    # --------------------------------------------------

    def _academic_reasoning(self, state):

        prediction = state.academic_risk

        lines = [

            f"Academic risk is {prediction.level} "
            f"(score {prediction.score:.2f})."

        ]

        for factor in prediction.top_factors:

            lines.append(

                f"{factor.factor} contributes "
                f"{factor.contribution}% "
                f"of academic risk."

            )

        return lines

    # --------------------------------------------------

    def _burnout_reasoning(self, state):

        prediction = state.burnout_risk

        lines = [

            f"Burnout risk is {prediction.level} "
            f"(score {prediction.score:.2f})."

        ]

        for factor in prediction.top_factors:

            lines.append(

                f"{factor.factor} contributes "
                f"{factor.contribution}% "
                f"of burnout risk."

            )

        return lines

    # --------------------------------------------------

    def _decision_reasoning(
        self,
        decisions,
    ):

        top = decisions[0]

        return [

            (
                f"{top.task['name']} has the highest "
                f"priority score "
                f"({top.priority_score:.2f})."
            ),

            (
                f"Policy Engine recommendation: "
                f"{top.action} "
                f"because {top.reason}"
            ),

        ]

    # --------------------------------------------------

    def _overall_strategy(
        self,
        state,
        decisions,
    ):

        top = decisions[0]

        return (

            f"ARWA recommends completing "
            f"{top.task['name']} first because it "
            f"provides the greatest expected academic "
            f"benefit while maintaining an appropriate "
            f"balance with burnout risk."

        )