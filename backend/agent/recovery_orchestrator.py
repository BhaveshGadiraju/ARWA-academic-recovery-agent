from agent.decision_engine import (
    DecisionEngine,
    Task,
    StudentState
)


class RecoveryOrchestrator:
    """
    Main AI agent responsible for coordinating
    the academic recovery pipeline.

    Pipeline:

    Student Data
        ↓
    Build Student State
        ↓
    Decision Engine
        ↓
    Recovery Plan
    """

    def __init__(self):
        self.decision_engine = DecisionEngine()

    def build_student_state(self, student_data):
        """
        Convert raw student data into the StudentState
        used by the AI agent.
        """

        return StudentState(
            academic_risk=student_data.get("academic_risk", 0.5),
            burnout_risk=student_data.get("burnout_risk", 0.5),
            available_time=student_data.get("available_time", 4.0)
        )

    def build_tasks(self, student_data):
        """
        Convert raw dictionaries into Task objects.
        """

        tasks = []

        for item in student_data.get("tasks", []):

            task = Task(
                id=item["id"],
                name=item["name"],
                points_value=item["points_value"],
                due_in_hours=item["due_in_hours"],
                estimated_time=item["estimated_time"],
                difficulty=item["difficulty"],
                late_penalty=item["late_penalty"],
                category=item["category"]
            )

            tasks.append(task)

        return tasks

    def generate_recovery_plan(self, decisions):
        """
        Convert AI decisions into a clean JSON response
        for the frontend.
        """

        plan = []

        for decision in decisions:

            plan.append({
                "task": decision.task.name,
                "action": decision.action,
                "priority_score": round(decision.priority_score, 2),
                "reason": decision.reason,
                "estimated_time": decision.task.estimated_time,
                "due_in_hours": decision.task.due_in_hours
            })

        return plan

    def run(self, student_data):
        """
        Main AI pipeline.
        """

        # Step 1
        state = self.build_student_state(student_data)

        # Step 2
        tasks = self.build_tasks(student_data)

        # Step 3
        decisions = self.decision_engine.optimize(tasks, state)

        # Step 4
        recovery_plan = self.generate_recovery_plan(decisions)

        return {
            "student_state": {
                "academic_risk": state.academic_risk,
                "burnout_risk": state.burnout_risk,
                "available_time": state.available_time
            },
            "recovery_plan": recovery_plan
        }
    