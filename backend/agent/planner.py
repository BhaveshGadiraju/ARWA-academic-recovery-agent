from typing import List
from datetime import datetime, timedelta


class ScheduledBlock:
    def __init__(self, task_name, start_time, end_time, reason):
        self.task_name = task_name
        self.start_time = start_time
        self.end_time = end_time
        self.reason = reason


class RecoveryPlan:
    def __init__(self, blocks, total_focus_time, break_time):
        self.blocks = blocks
        self.total_focus_time = total_focus_time
        self.break_time = break_time


class Planner:
    """
    Converts ranked decisions into a structured daily schedule.
    """

    def __init__(self):

        self.default_session_length = 60  # minutes
        self.break_length = 15  # minutes

    # -------------------------
    # CORE PLANNING LOGIC
    # -------------------------
    def generate(self, decisions, available_time: float):

        schedule = []

        current_time = datetime.now()

        used_time = 0

        for decision in decisions:

            task = decision.task

            if decision.action == "DROP":
                continue

            estimated_minutes = int(task["estimated_time"] * 60)

            # cap session length
            session_time = min(
                estimated_minutes,
                self.default_session_length
            )

            start_time = current_time + timedelta(minutes=used_time)
            end_time = start_time + timedelta(minutes=session_time)

            schedule.append(
                ScheduledBlock(
                    task_name=task["name"],
                    start_time=start_time,
                    end_time=end_time,
                    reason=decision.reason
                )
            )

            used_time += session_time + self.break_length

            # stop if out of time
            if used_time > available_time * 60:
                break

        return RecoveryPlan(
            blocks=schedule,
            total_focus_time=used_time,
            break_time=self.break_length
        )