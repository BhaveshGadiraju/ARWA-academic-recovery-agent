from agent.feature_extractor import FeatureExtractor
from agent.decision_engine import DecisionEngine
from agent.reasoning_engine import ReasoningEngine
from agent.reflection_engine import ReflectionEngine
from agent.planner import Planner
from agent.explanation_engine import ExplanationEngine
from agent.experience_memory import ExperienceMemory

from models.academic_risk_model import AcademicRiskModel
from models.burnout_risk_model import BurnoutRiskModel
from models.state_vector import StudentState


class RecoveryOrchestrator:
    """
    Master AI agent responsible for coordinating
    the complete academic recovery pipeline.
    """

    def __init__(self):

        self.feature_extractor = FeatureExtractor()

        self.academic_model = AcademicRiskModel()

        self.burnout_model = BurnoutRiskModel()

        self.decision_engine = DecisionEngine()

        self.planner = Planner()

        self.reasoning_engine = ReasoningEngine()

        self.reflection_engine = ReflectionEngine()

        self.explanation_engine = ExplanationEngine()

        self.memory = ExperienceMemory()

    # --------------------------------------------------

    def run(
        self,
        student_data,
    ):

        # ----------------------------------------------
        # Phase 1
        # Perception
        # ----------------------------------------------

        features = self.feature_extractor.extract(
            student_data
        )

        # ----------------------------------------------
        # Phase 2
        # Prediction
        # ----------------------------------------------

        academic_prediction = self.academic_model.predict(
            features
        )

        burnout_prediction = self.burnout_model.predict(
            features
        )

        # ----------------------------------------------
        # Phase 3
        # State Construction
        # ----------------------------------------------

        state = StudentState(

            tasks=student_data.tasks,

            academic_risk=academic_prediction,

            burnout_risk=burnout_prediction,

        )

        # ----------------------------------------------
        # Phase 4
        # Optimization
        # ----------------------------------------------

        decisions = self.decision_engine.optimize(
            state
        )

        # ----------------------------------------------
        # Phase 5
        # Planning
        # ----------------------------------------------

        plan = self.planner.generate(
            decisions
        )

        # ----------------------------------------------
        # Phase 6
        # Explainability
        # ----------------------------------------------

        reasoning = self.reasoning_engine.generate_reasoning(
            state,
            decisions,
        )

        explanations = self.explanation_engine.generate(
            decisions
        )

        # ----------------------------------------------
        # Phase 7
        # Reflection
        # ----------------------------------------------

        reflection = self.reflection_engine.reflect(
            state,
            decisions,
        )

        # ----------------------------------------------
        # Phase 8
        # Memory
        # ----------------------------------------------

        self.memory.store(

            state=state,

            decisions=decisions,

            reflection=reflection,

        )

        # ----------------------------------------------
        # Final Output
        # ----------------------------------------------

        return {

            "features": features,

            "academic_prediction": academic_prediction,

            "burnout_prediction": burnout_prediction,

            "state": state,

            "decisions": decisions,

            "plan": plan,

            "reasoning": reasoning,

            "explanations": explanations,

            "reflection": reflection,

        }