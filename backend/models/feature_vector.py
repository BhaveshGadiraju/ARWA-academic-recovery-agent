from dataclasses import dataclass


@dataclass
class FeatureVector:
    """
    Standardized feature representation used by all AI models.
    """

    current_grade: float

    missing_tasks: int

    estimated_workload: float

    average_difficulty: float

    deadline_density: float

    stress_level: float

    available_time: float