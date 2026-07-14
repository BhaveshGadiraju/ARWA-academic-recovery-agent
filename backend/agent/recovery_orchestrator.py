from agent.feature_extractor import FeatureExtractor
from agent.decision_engine import DecisionEngine
from agent.reasoning_engine import ReasoningEngine
from agent.reflection_engine import ReflectionEngine
from agent.planner import Planner
from agent.explanation_engine import ExplanationEngine
from agent.experience_memory import ExperienceMemory
from agent.simulation_engine import SimulationEngine
from agent.recovery_score import RecoveryScoreEngine
from agent.recovery_forecast import RecoveryForecastEngine
from agent.strategy_comparison import StrategyComparisonEngine
from agent.report_generator import ReportGenerator

from models.academic_risk_model import AcademicRiskModel
from models.burnout_risk_model import BurnoutRiskModel
from models.state_vector import StateVectorBuilder


class RecoveryOrchestrator:
    """
    Master AI pipeline for ARWA.

    Coordinates every stage of the academic
    recovery process from perception through
    planning, simulation, forecasting, and
    explainability.
    """

    def __init__(self):

        self.feature_extractor = FeatureExtractor()

        self.academic_model = AcademicRiskModel()

        self.burnout_model = BurnoutRiskModel()

        self.state_builder = StateVectorBuilder()

        self.decision_engine = DecisionEngine()

        self.planner = Planner()

        self.simulation_engine = SimulationEngine()

        self.strategy_comparison = StrategyComparisonEngine()

        self.recovery_score = RecoveryScoreEngine()

        self.recovery_forecast = RecoveryForecastEngine()

        self.reasoning_engine = ReasoningEngine()

        self.explanation_engine = ExplanationEngine()

        self.reflection_engine = ReflectionEngine()

        self.memory = ExperienceMemory()

        self.report_generator = ReportGenerator()

    # --------------------------------------------------

    def run(
        self,
        student_data,
    ):

        # ==================================================
        # Phase 1 — Feature Extraction
        # ==================================================

        features = self.feature_extractor.extract(
            student_data
        )

        # ==================================================
        # Phase 2 — Risk Prediction
        # ==================================================

        academic_prediction = self.academic_model.predict(
            features
        )

        burnout_prediction = self.burnout_model.predict(
            features
        )

        # ==================================================
        # Phase 3 — Build Student State
        # ==================================================

        state = self.state_builder.build(

            features=features,

            academic_prediction=academic_prediction,

            burnout_prediction=burnout_prediction,

            tasks=student_data.get('tasks', []),

        )

        # ==================================================
        # Phase 4 — AI Decision Engine
        # ==================================================

        decisions = self.decision_engine.optimize(
            state
        )

        # ==================================================
        # Phase 5 — Planner
        # ==================================================

        plan = self.planner.generate(
            decisions,
            state.available_time
        )

        # ==================================================
        # Phase 6 — Simulation
        # ==================================================

        simulations = self.simulation_engine.simulate(

            state,

            decisions,

        )

        if simulations:

            best_strategy = simulations[0]

        else:

            best_strategy = None

        # ==================================================
        # Phase 7 — Strategy Comparison
        # ==================================================

        strategies = self.strategy_comparison.compare(

            simulations,

        )

        # ==================================================
        # Phase 8 — Recovery Score
        # ==================================================

        current_score = self.recovery_score.calculate_current(

            state,

        )

        projected_score = self.recovery_score.calculate_projected(

            state,

            best_strategy,

        )

        recovery_score = self.recovery_score.calculate_improvement(

            current_score,

            projected_score,

        )

        # ==================================================
        # Phase 9 — Recovery Forecast
        # ==================================================

        forecast = self.recovery_forecast.forecast(

            state,

            best_strategy,

            recovery_score["after"],

        )

        # ==================================================
        # Phase 10 — AI Report
        # ==================================================

        report = self.report_generator.generate(

            academic_prediction,

            burnout_prediction,

            recovery_score,

            forecast,

            strategies,

        )

        # ==================================================
        # Phase 11 — Explainability
        # ==================================================

        reasoning = self.reasoning_engine.generate_reasoning(

            state,

            decisions,

        )

        explanations = self.explanation_engine.generate(

            decisions,

        )

        # ==================================================
        # Phase 12 — Reflection
        # ==================================================

        reflection = self.reflection_engine.reflect(

            state,

            decisions,

        )

        # ==================================================
        # Phase 13 — Memory
        # ==================================================

        # Store outcome metrics from the analysis
        outcome_metrics = {
            "recovery_score": recovery_score,
            "reflection": reflection,
        }

        self.memory.store(
            state=state,
            plan=plan,
            outcome_metrics=outcome_metrics,
        )

        # ==================================================
        # Final Output
        # ==================================================

        return {

            "report": report,

            "features": features,

            "state": state,

            "academic_prediction": academic_prediction,

            "burnout_prediction": burnout_prediction,

            "decisions": decisions,

            "plan": plan,

            "simulations": simulations,

            "strategies": strategies,

            "best_strategy": best_strategy,

            "recovery_score": recovery_score,

            "forecast": forecast,

            "reasoning": reasoning,

            "explanations": explanations,

            "reflection": reflection,

        }