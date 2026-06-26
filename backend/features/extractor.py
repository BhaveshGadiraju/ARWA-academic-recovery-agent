from typing import Dict, List


class FeatureExtractor:
    """
    Converts raw student data into AI-ready features.
    """

    def extract(self, student_data: Dict):

        tasks = student_data.get("tasks", [])

        total_tasks = len(tasks)

        if total_tasks == 0:
            return {
                "total_tasks": 0,
                "missing_tasks": 0,
                "total_points": 0,
                "average_difficulty": 0,
                "average_due_time": 0,
                "estimated_workload": 0,
                "deadline_density": 0
            }

        missing_tasks = 0
        total_points = 0
        total_difficulty = 0
        total_time = 0
        due_sum = 0

        for task in tasks:

            total_points += task["points_value"]

            total_difficulty += task["difficulty"]

            total_time += task["estimated_time"]

            due_sum += task["due_in_hours"]

            if task.get("missing", False):
                missing_tasks += 1

        average_difficulty = total_difficulty / total_tasks

        average_due_time = due_sum / total_tasks

        deadline_density = total_tasks / max(average_due_time, 1)

        return {

            "total_tasks": total_tasks,

            "missing_tasks": missing_tasks,

            "total_points": total_points,

            "average_difficulty": average_difficulty,

            "average_due_time": average_due_time,

            "estimated_workload": total_time,

            "deadline_density": deadline_density,

            "available_time": student_data.get(
                "available_time",
                4
            ),

            "current_grade": student_data.get(
                "current_grade",
                85
            ),

            "stress_level": student_data.get(
                "stress_level",
                5
            )
        }