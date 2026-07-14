from agent.recovery_orchestrator import RecoveryOrchestrator


class RecoveryController:

    def __init__(self):

        self.agent = RecoveryOrchestrator()

    def analyze(

        self,

        student_data,

    ):

        # Convert Pydantic model to dict for backend compatibility.
        # RecoveryOrchestrator and FeatureExtractor expect dictionaries.
        if hasattr(student_data, 'dict'):
            # Pydantic v1
            student_dict = student_data.dict()
        elif hasattr(student_data, 'model_dump'):
            # Pydantic v2
            student_dict = student_data.model_dump()
        else:
            # Already a dict
            student_dict = student_data

        # Transform assignments to tasks format expected by backend.
        # Frontend sends: title, course, difficulty, estimated_hours, days_remaining, completed
        # Backend expects: difficulty, estimated_time, due_in_hours, points_value, (optional) missing
        if 'assignments' in student_dict:
            assignments = student_dict['assignments']
            tasks = []
            for i, assignment in enumerate(assignments):
                # Convert assignment dict/obj to task dict
                if hasattr(assignment, 'dict'):
                    asgn = assignment.dict()
                elif hasattr(assignment, 'model_dump'):
                    asgn = assignment.model_dump()
                else:
                    asgn = assignment

                task = {
                    'title': asgn.get('title', f'Assignment {i}'),
                    'difficulty': asgn.get('difficulty', 0.5),
                    'estimated_time': asgn.get('estimated_hours', 3),
                    'due_in_hours': asgn.get('days_remaining', 7) * 24,  # Convert days to hours
                    'points_value': 10,  # Default points per assignment
                    'missing': not asgn.get('completed', False),  # Incomplete = missing
                }
                tasks.append(task)
            student_dict['tasks'] = tasks
            # Remove assignments as tasks is what backend expects
            del student_dict['assignments']

        return self.agent.run(

            student_dict,

        )