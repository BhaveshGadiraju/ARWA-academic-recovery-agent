class RecoveryController:

    def __init__(self):
        self._analysis_service = None

    @property
    def analysis_service(self):
        if self._analysis_service is None:
            from backend.services.analysis_service import AnalysisService
            self._analysis_service = AnalysisService()
        return self._analysis_service

    async def analyze(self, student_data):
        if hasattr(student_data, 'model_dump'):
            student_dict = student_data.model_dump()
        elif hasattr(student_data, 'dict'):
            student_dict = student_data.dict()
        else:
            student_dict = student_data

        if 'assignments' in student_dict:
            assignments = student_dict['assignments']
            tasks = []
            for i, assignment in enumerate(assignments):
                if hasattr(assignment, 'model_dump'):
                    asgn = assignment.model_dump()
                elif hasattr(assignment, 'dict'):
                    asgn = assignment.dict()
                else:
                    asgn = assignment

                task = {
                    'name': asgn.get('title', f'Assignment {i}'),
                    'title': asgn.get('title', f'Assignment {i}'),
                    'course': asgn.get('course', 'Unknown'),
                    'difficulty': asgn.get('difficulty', 0.5),
                    'estimated_time': asgn.get('estimated_hours', 3),
                    'due_in_hours': asgn.get('days_remaining', 7) * 24,
                    'points_value': 10,
                    'missing': not asgn.get('completed', False),
                }
                tasks.append(task)
            student_dict['tasks'] = tasks
            del student_dict['assignments']

        result = await self.analysis_service.analyze(student_dict)
        return result
