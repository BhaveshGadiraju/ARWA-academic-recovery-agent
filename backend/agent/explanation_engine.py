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