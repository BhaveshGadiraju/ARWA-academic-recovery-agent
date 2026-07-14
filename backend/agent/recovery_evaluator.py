from typing import List


class RecoveryEvaluator:
    """
    Scores an entire recovery strategy by balancing:

    - Academic improvement
    - Burnout
    - Time efficiency
    - Deadline pressure

    This evaluator becomes the objective function
    for the Simulation Engine.
    """

    def evaluate(
        self,
        tasks: List,
        state,
    ):

        grade_gain = self._estimate_grade_gain(tasks)

        burnout = self._estimate_burnout(tasks, state)

        time_cost = self._estimate_time(tasks)

        urgency_bonus = self._estimate_urgency(tasks)

        recovery_score = (

            grade_gain * 4.0

            + urgency_bonus * 2.5

            - burnout * 3.0

            - time_cost * 1.5

        )

        return {

            "grade_gain": round(grade_gain, 2),

            "burnout": round(burnout, 2),

            "time_cost": round(time_cost, 2),

            "urgency_bonus": round(urgency_bonus, 2),

            "recovery_score": round(recovery_score, 2),

        }

    # -----------------------------------------

    def _estimate_grade_gain(
        self,
        tasks,
    ):

        return sum(
            t["points_value"]
            for t in tasks
        ) / 10

    # -----------------------------------------

    def _estimate_burnout(
        self,
        tasks,
        state,
    ):

        workload = sum(
            t["estimated_time"]
            for t in tasks
        )

        burnout = (

            state.burnout_risk.score

            + workload / 20

        )

        return min(
            burnout,
            1.0,
        )

    # -----------------------------------------

    def _estimate_time(
        self,
        tasks,
    ):

        return sum(
            t["estimated_time"]
            for t in tasks
        )

    # -----------------------------------------

    def _estimate_urgency(
        self,
        tasks,
    ):

        bonus = 0

        for task in tasks:

            if task["due_in_hours"] <= 24:
                bonus += 2

            elif task["due_in_hours"] <= 72:
                bonus += 1

        return bonus