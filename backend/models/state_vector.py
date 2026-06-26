from dataclasses import dataclass
from typing import Dict, List


@dataclass
class StudentState:
    """
    Represents ARWA's complete understanding of the student's
    current academic and wellness situation.
    """

    # Original extracted features
    features: Dict

    # AI model predictions
    academic_risk: object
    burnout_risk: object

    # Original tasks
    tasks: List[Dict]

    # Student resources
    available_time: float

    # Current grade
    current_grade: float

    # Wellness
    stress_level: float

class StateVectorBuilder:
    """
    Combines extracted features and AI predictions into one object.
    """

    def build(
        self,
        features,
        academic_prediction,
        burnout_prediction,
        tasks
    ):

        return StudentState(

            features=features,

            academic_risk=academic_prediction,

            burnout_risk=burnout_prediction,

            tasks=tasks,

            available_time=features["available_time"],

            current_grade=features["current_grade"],

            stress_level=features["stress_level"]

        )