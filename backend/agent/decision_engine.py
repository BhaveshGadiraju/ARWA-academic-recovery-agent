from typing import List
import math

from models.state_vector import StudentState
from models.agent_prediction import ContributingFactor
from agent.policy_engine import PolicyEngine


class TaskDecision:
    """
    Final decision produced after task scoring and policy evaluation.
    """

    def __init__(
        self,
        task,
        priority_score,
        action,
        reason,
        factors,
        confidence,
    ):
        self.task = task
        self.priority_score = priority_score
        self.action = action
        self.reason = reason
        self.factors = factors
        self.confidence = confidence


class DecisionEngine:
    """
    Scores and ranks academic tasks.

    NOTE:
    This class DOES NOT decide whether a task should
    be DO / DELAY / DROP.

    That responsibility belongs to the PolicyEngine.
    """

    def __init__(self):

        self.policy_engine = PolicyEngine()

        self.weights = {
            "grade_impact": 1.5,
            "urgency": 2.0,
            "difficulty_penalty": 1.0,
            "burnout_penalty": 2.5,
        }

    # ----------------------------------------
    # Feature Engineering
    # ----------------------------------------

    def compute_task_features(
        self,
        task,
        state: StudentState,
    ):

        urgency = math.exp(
            -task["due_in_hours"] / 24
        )

        grade_impact = (
            task["points_value"]
            * self.weights["grade_impact"]
        )

        difficulty_penalty = (
            task["difficulty"] / 10
        )

        burnout_factor = (
            state.burnout_risk.score
            * task["estimated_time"]
        )

        return {

            "urgency": urgency,

            "grade_impact": grade_impact,

            "difficulty_penalty": difficulty_penalty,

            "burnout_factor": burnout_factor,

        }

    # ----------------------------------------
    # Optimization
    # ----------------------------------------

    def score_task(
        self,
        task,
        state: StudentState,
    ):

        f = self.compute_task_features(
            task,
            state,
        )

        score = (

            f["grade_impact"]

            * f["urgency"]

            * self.weights["urgency"]

        ) / (

            task["estimated_time"]

            + f["difficulty_penalty"]

            + (
                f["burnout_factor"]
                * self.weights["burnout_penalty"]
            )

        )

        if (
            state.burnout_risk.score > 0.70
            and task["difficulty"] > 7
        ):
            score *= 0.5

        if task["due_in_hours"] < 6:
            score *= 2.0

        return score, f

    # ----------------------------------------
    # Main Optimization Loop
    # ----------------------------------------

    def optimize(
        self,
        state: StudentState,
    ):

        decisions: List[TaskDecision] = []

        for task in state.tasks:

            score, features = self.score_task(
                task,
                state,
            )

            policy = self.policy_engine.evaluate(
                task,
                score,
                state,
            )

            explanation_factors = [

                ContributingFactor(
                    factor="Urgency",
                    contribution=round(
                        features["urgency"] * 100,
                        1,
                    ),
                    explanation="Deadline proximity."
                ),

                ContributingFactor(
                    factor="Grade Impact",
                    contribution=round(
                        features["grade_impact"],
                        1,
                    ),
                    explanation="Estimated effect on course grade."
                ),

                ContributingFactor(
                    factor="Burnout Cost",
                    contribution=round(
                        features["burnout_factor"],
                        1,
                    ),
                    explanation="Estimated mental workload."
                ),

            ]

            decisions.append(

                TaskDecision(

                    task=task,

                    priority_score=round(
                        score,
                        2,
                    ),

                    action=policy.action,

                    reason=policy.reason,

                    confidence=policy.confidence,

                    factors=explanation_factors,

                )

            )

        decisions.sort(
            key=lambda x: x.priority_score,
            reverse=True,
        )

        return decisions