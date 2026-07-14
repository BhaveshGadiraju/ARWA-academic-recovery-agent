from typing import List


class ExplanationEngine:
    """
    Converts ARWA's internal decisions into human-readable reasoning.
    """

    # -------------------------
    # TASK EXPLANATION
    # -------------------------
    def explain_task_decision(self, decision):

        task = decision.task

        explanation = []

        explanation.append(
            f"Task: {task['name']}"
        )

        explanation.append(
            f"Action: {decision.action}"
        )

        explanation.append(
            f"Reason: {decision.reason}"
        )

        explanation.append("Key contributing factors:")

        for factor in decision.factors:

            explanation.append(
                f"- {factor.factor}: {factor.explanation}"
            )

        return "\n".join(explanation)

    # -------------------------
    # FULL PLAN EXPLANATION
    # -------------------------
    def explain_plan(self, recovery_plan):

        lines = []

        lines.append("📊 ARWA Recovery Plan Explanation\n")

        for block in recovery_plan.blocks:

            lines.append(
                f"{block.start_time.strftime('%H:%M')} - "
                f"{block.end_time.strftime('%H:%M')} → "
                f"{block.task_name}"
            )

            lines.append(
                f"Reason: {block.reason}\n"
            )

        lines.append(
            f"Total focus time: {recovery_plan.total_focus_time} minutes"
        )

        lines.append(
            f"Break length: {recovery_plan.break_time} minutes"
        )

        return "\n".join(lines)

    # -------------------------
    # DECISIONS EXPLANATION
    # -------------------------
    def generate(self, decisions):
        """Generate explanations for a set of decisions."""
        if not decisions:
            return {"explanation": "No decisions to explain"}
        
        # If decisions is a list, explain each one
        if isinstance(decisions, list):
            explanations = []
            for decision in decisions:
                # Handle both dict and object formats
                if hasattr(decision, 'task') and hasattr(decision, 'action'):
                    explanations.append(self.explain_task_decision(decision))
                elif isinstance(decision, dict):
                    # For dict format, create a simple explanation
                    explanations.append(f"Decision: {decision.get('action', 'N/A')}")
            return {"explanations": explanations}
        
        # If decisions is a dict, treat it as a single decision container
        if isinstance(decisions, dict):
            return {"explanation": f"Strategy applied with {len(decisions.get('tasks', []))} tasks"}
        
        # Fallback
        return {"explanation": "Decision process completed"}