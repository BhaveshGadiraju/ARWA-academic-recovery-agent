from dataclasses import dataclass
from typing import List
import math


@dataclass
class Task:
    id: str
    name: str
    points_value: float
    due_in_hours: float
    estimated_time: float
    difficulty: float  # 1-10
    late_penalty: float
    category: str  # homework, quiz, exam


@dataclass
class StudentState:
    academic_risk: float   # 0–1
    burnout_risk: float    # 0–1
    available_time: float  # hours today


@dataclass
class TaskDecision:
    task: Task
    priority_score: float
    action: str   # DO / DELAY / DROP
    reason: str


class DecisionEngine:

    def __init__(self):
        self.weights = {
            "grade_impact": 1.5,
            "urgency": 2.0,
            "difficulty_penalty": 1.0,
            "burnout_penalty": 2.5,
        }

    def compute_features(self, task: Task, state: StudentState):

        urgency = math.exp(-task.due_in_hours / 24)

        grade_impact = task.points_value * self.weights["grade_impact"]

        difficulty_penalty = task.difficulty / 10

        burnout_factor = state.burnout_risk * task.estimated_time

        return {
            "urgency": urgency,
            "grade_impact": grade_impact,
            "difficulty_penalty": difficulty_penalty,
            "burnout_factor": burnout_factor
        }

    def score_task(self, task: Task, state: StudentState):

        f = self.compute_features(task, state)

        score = (
            f["grade_impact"] * f["urgency"] * self.weights["urgency"]
        ) / (
            task.estimated_time
            + f["difficulty_penalty"]
            + f["burnout_factor"] * self.weights["burnout_penalty"]
        )

        if state.burnout_risk > 0.7 and task.difficulty > 7:
            score *= 0.5

        if task.due_in_hours < 6:
            score *= 2.0

        return score

    def decide_action(self, task: Task, score: float, state: StudentState):

        if task.points_value < 5 and task.due_in_hours > 48:
            return "DROP", "Low impact and not urgent"

        if state.burnout_risk > 0.8 and task.difficulty > 7:
            return "DELAY", "High burnout risk detected"

        if task.due_in_hours < 8:
            return "DO", "Deadline critical"

        if score > 8:
            return "DO", "High priority recovery task"

        return "DELAY", "Lower priority than alternatives"

    def optimize(self, tasks: List[Task], state: StudentState):

        decisions = []

        for task in tasks:
            score = self.score_task(task, state)
            action, reason = self.decide_action(task, score, state)

            decisions.append(
                TaskDecision(
                    task=task,
                    priority_score=score,
                    action=action,
                    reason=reason
                )
            )

        decisions.sort(key=lambda x: x.priority_score, reverse=True)

        return decisions
    