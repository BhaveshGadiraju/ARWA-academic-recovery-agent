from dataclasses import dataclass
from typing import Dict


@dataclass
class BurnoutPrediction:
    risk_score: float
    risk_level: str
    confidence: float


class BurnoutRiskModel:
    """
    Estimates student burnout risk using workload,
    stress, deadlines, and available study time.
    """

    def __init__(self):

        self.weights = {

            "estimated_workload": 0.35,

            "stress_level": 0.30,

            "available_time": 0.15,

            "average_difficulty": 0.10,

            "deadline_density": 0.10

        }

    def normalize_workload(self, workload):

        return min(workload / 20, 1.0)

    def normalize_stress(self, stress):

        return min(stress / 10, 1.0)

    def normalize_available_time(self, hours):

        return max(0.0, 1 - (hours / 8))

    def normalize_difficulty(self, difficulty):

        return difficulty / 10

    def normalize_deadline_density(self, density):

        return min(density, 1.0)

    def classify_risk(self, score):

        if score >= 0.80:
            return "CRITICAL"

        if score >= 0.60:
            return "HIGH"

        if score >= 0.40:
            return "MEDIUM"

        return "LOW"

    def calculate_confidence(self, features):

        available = sum(
            value is not None
            for value in features.values()
        )

        return round(
            available / len(features),
            2
        )

    def predict(self, features: Dict):

        workload = self.normalize_workload(
            features["estimated_workload"]
        )

        stress = self.normalize_stress(
            features["stress_level"]
        )

        available_time = self.normalize_available_time(
            features["available_time"]
        )

        difficulty = self.normalize_difficulty(
            features["average_difficulty"]
        )

        density = self.normalize_deadline_density(
            features["deadline_density"]
        )

        risk_score = (

            workload * self.weights["estimated_workload"]

            + stress * self.weights["stress_level"]

            + available_time * self.weights["available_time"]

            + difficulty * self.weights["average_difficulty"]

            + density * self.weights["deadline_density"]

        )

        risk_level = self.classify_risk(
            risk_score
        )

        confidence = self.calculate_confidence(
            features
        )

        return BurnoutPrediction(
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            confidence=confidence
        )