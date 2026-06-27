from typing import Dict

from models.agent_prediction import (
    AgentPrediction,
    ContributingFactor,
)


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
            "deadline_density": 0.10,
        }

    # --------------------------------------------------
    # Normalization
    # --------------------------------------------------

    def normalize_workload(self, workload):

        return min(
            workload / 20,
            1.0,
        )

    def normalize_stress(self, stress):

        return min(
            stress / 10,
            1.0,
        )

    def normalize_available_time(self, hours):

        return max(
            0.0,
            1 - (hours / 8),
        )

    def normalize_difficulty(self, difficulty):

        return difficulty / 10

    def normalize_deadline_density(self, density):

        return min(
            density,
            1.0,
        )

    # --------------------------------------------------
    # Risk Classification
    # --------------------------------------------------

    def classify_risk(self, score):

        if score >= 0.80:
            return "CRITICAL"

        if score >= 0.60:
            return "HIGH"

        if score >= 0.40:
            return "MEDIUM"

        return "LOW"

    # --------------------------------------------------
    # Confidence
    # --------------------------------------------------

    def calculate_confidence(self, features):

        available = sum(
            value is not None
            for value in features.values()
        )

        return round(
            available / len(features),
            2,
        )

    # --------------------------------------------------
    # Prediction
    # --------------------------------------------------

    def predict(
        self,
        features: Dict,
    ):

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

        # --------------------------------------------------
        # Dynamic Explainability (True Percentages)
        # --------------------------------------------------

        raw_contributions = {

            "Estimated Workload":
                workload * self.weights["estimated_workload"],

            "Stress Level":
                stress * self.weights["stress_level"],

            "Available Time":
                available_time * self.weights["available_time"],

            "Average Difficulty":
                difficulty * self.weights["average_difficulty"],

            "Deadline Density":
                density * self.weights["deadline_density"],

        }

        total = sum(
            raw_contributions.values()
        )

        explanations = {

            "Estimated Workload":
                "Heavy workload increases burnout risk.",

            "Stress Level":
                "Higher stress significantly impacts burnout.",

            "Available Time":
                "Limited study time increases pressure.",

            "Average Difficulty":
                "More difficult work increases fatigue.",

            "Deadline Density":
                "Many nearby deadlines increase stress.",

        }

        contributions = []

        for factor, value in raw_contributions.items():

            percentage = 0.0

            if total > 0:

                percentage = round(
                    value / total * 100,
                    1,
                )

            contributions.append(

                ContributingFactor(

                    factor=factor,

                    contribution=percentage,

                    explanation=explanations[factor],

                )

            )

        top_factors = sorted(

            contributions,

            key=lambda factor: factor.contribution,

            reverse=True,

        )[:3]

        reasoning = [

            f"Burnout risk classified as {risk_level}.",

            "Risk is computed using normalized wellness indicators.",

            (
                f"The largest contributors are "
                f"{top_factors[0].factor}, "
                f"{top_factors[1].factor}, "
                f"and {top_factors[2].factor}."
            ),

        ]

        return AgentPrediction(

            score=round(
                risk_score,
                2,
            ),

            level=risk_level,

            confidence=confidence,

            top_factors=top_factors,

            reasoning=reasoning,

        )