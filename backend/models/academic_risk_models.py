from typing import Dict

from models.agent_prediction import (
    AgentPrediction,
    ContributingFactor,
)


class AcademicRiskModel:
    """
    Predicts the student's academic risk using
    engineered features from the FeatureExtractor.
    """

    def __init__(self):

        self.weights = {
            "missing_tasks": 0.30,
            "current_grade": 0.30,
            "deadline_density": 0.15,
            "estimated_workload": 0.15,
            "average_difficulty": 0.10,
        }

    # --------------------------------------------------
    # Normalization Functions
    # --------------------------------------------------

    def normalize_grade(self, grade):

        return max(
            0.0,
            min(1.0, (100 - grade) / 100),
        )

    def normalize_missing_tasks(self, missing_tasks):

        return min(
            missing_tasks / 10,
            1.0,
        )

    def normalize_workload(self, workload):

        return min(
            workload / 20,
            1.0,
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

        grade = self.normalize_grade(
            features["current_grade"]
        )

        missing = self.normalize_missing_tasks(
            features["missing_tasks"]
        )

        workload = self.normalize_workload(
            features["estimated_workload"]
        )

        difficulty = self.normalize_difficulty(
            features["average_difficulty"]
        )

        density = self.normalize_deadline_density(
            features["deadline_density"]
        )

        risk_score = (

            grade * self.weights["current_grade"]

            + missing * self.weights["missing_tasks"]

            + workload * self.weights["estimated_workload"]

            + density * self.weights["deadline_density"]

            + difficulty * self.weights["average_difficulty"]

        )

        risk_level = self.classify_risk(
            risk_score
        )

        confidence = self.calculate_confidence(
            features
        )

        # --------------------------------------------------
        # Dynamic Explainability
         # --------------------------------------------------

        raw_contributions = {

            "Current Grade":
                grade * self.weights["current_grade"],

            "Missing Assignments":
                missing * self.weights["missing_tasks"],

            "Estimated Workload":
                workload * self.weights["estimated_workload"],

            "Deadline Density":
                density * self.weights["deadline_density"],

            "Average Difficulty":
                difficulty * self.weights["average_difficulty"],

        }

        total = sum(raw_contributions.values())

        explanations = {

            "Current Grade":
                "Lower grades increase academic risk.",

            "Missing Assignments":
                "Missing work strongly affects academic recovery.",

            "Estimated Workload":
                "Heavy workload makes recovery more difficult.",

            "Deadline Density":
                "Many nearby deadlines increase academic pressure.",

            "Average Difficulty":
                "More difficult assignments increase recovery effort.",

        }

        contributions = []

        for factor, value in raw_contributions.items():

            percentage = 0

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

            key=lambda x: x.contribution,

            reverse=True,

        )[:3]

        reasoning = [

            f"Overall academic risk classified as {risk_level}.",

            "Risk is computed using normalized academic indicators.",

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