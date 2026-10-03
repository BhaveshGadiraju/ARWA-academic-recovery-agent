"""
ARWA Persistence Service.

Saves completed analysis results to Supabase.
Only called when a user is authenticated.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.services.supabase_client import get_user_client

logger = logging.getLogger(__name__)


async def persist_analysis(
    user_id: str,
    access_token: str,
    student_data: Dict[str, Any],
    result: Dict[str, Any],
) -> Optional[str]:
    """Save a completed analysis and its results to the database.

    Args:
        user_id: The authenticated user's ID.
        access_token: The user's JWT access token.
        student_data: The original input data (tasks, grade, stress, etc.).
        result: The ARWAAssessment response.

    Returns:
        The analysis ID if successful, None otherwise.
    """
    try:
        client = get_user_client(access_token)

        # 1. Insert the analysis record
        analysis_row = {
            'user_id': user_id,
            'current_grade': student_data.get('current_grade', 0),
            'stress_level': student_data.get('stress_level', 5),
            'available_time': student_data.get('available_time', 4),
            'ai_powered': result.get('ai_powered', False),
            'fallback_used': result.get('fallback_used', False),
            'overall_summary': result.get('overall_summary', ''),
            'academic_risk_score': result.get('academic_risk', {}).get('score', 50),
            'academic_risk_level': result.get('academic_risk', {}).get('level', 'MODERATE'),
            'academic_risk_explanation': result.get('academic_risk', {}).get('explanation', ''),
            'burnout_risk_score': result.get('burnout_risk', {}).get('score', 50),
            'burnout_risk_level': result.get('burnout_risk', {}).get('level', 'MODERATE'),
            'burnout_risk_explanation': result.get('burnout_risk', {}).get('explanation', ''),
            'recovery_score_value': result.get('recovery_score', {}).get('score', 50),
            'recovery_score_explanation': result.get('recovery_score', {}).get('explanation', ''),
        }

        analysis_response = client.table('analyses').insert(analysis_row).execute()
        analysis_id = analysis_response.data[0]['id']
        logger.info(f"Persisted analysis {analysis_id} for user {user_id}")

        # 2. Insert analysis assignments (snapshot of input)
        # student.model_dump() uses key 'assignments' with fields:
        #   title, course, difficulty, estimated_hours, days_remaining, completed
        assignments = student_data.get('assignments', student_data.get('tasks', []))
        if assignments:
            aa_rows = []
            for t in assignments:
                aa_rows.append({
                    'analysis_id': analysis_id,
                    'title': t.get('name', t.get('title', 'Unknown')),
                    'course': t.get('course', 'Unknown'),
                    'difficulty': t.get('difficulty', 0.5),
                    'estimated_hours': t.get('estimated_hours', t.get('estimated_time', 0)),
                    'days_remaining': t.get('days_remaining', t.get('due_in_hours', 168) // 24),
                    'completed': t.get('completed', not t.get('missing', True)),
                })
            client.table('analysis_assignments').insert(aa_rows).execute()

        # 3. Insert risk factors
        risk_factors = result.get('risk_factors', [])
        if risk_factors:
            rf_rows = []
            for rf in risk_factors:
                rf_rows.append({
                    'analysis_id': analysis_id,
                    'factor': rf.get('factor', ''),
                    'severity': rf.get('severity', 'LOW'),
                    'impact': rf.get('impact', 0),
                    'evidence': rf.get('evidence', ''),
                    'explanation': rf.get('explanation', ''),
                })
            client.table('risk_factors').insert(rf_rows).execute()

        # 4. Insert priorities
        priorities = result.get('priorities', [])
        if priorities:
            pri_rows = []
            for p in priorities:
                pri_rows.append({
                    'analysis_id': analysis_id,
                    'rank': p.get('rank', 1),
                    'course_or_task': p.get('course_or_task', ''),
                    'priority': p.get('priority', 'LOW'),
                    'reason': p.get('reason', ''),
                })
            client.table('priorities').insert(pri_rows).execute()

        # 5. Insert recommendations
        recommendations = result.get('recommendations', [])
        if recommendations:
            rec_rows = []
            for r in recommendations:
                rec_rows.append({
                    'analysis_id': analysis_id,
                    'action': r.get('action', ''),
                    'reason': r.get('reason', ''),
                    'priority': r.get('priority', 'LOW'),
                    'expected_impact': r.get('expected_impact', ''),
                })
            client.table('recommendations').insert(rec_rows).execute()

        # 6. Insert recovery plan (days + tasks)
        recovery_plan = result.get('recovery_plan', [])
        if recovery_plan:
            for day in recovery_plan:
                day_response = client.table('recovery_plan_days').insert({
                    'analysis_id': analysis_id,
                    'date': day.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'total_study_minutes': day.get('total_study_minutes', 0),
                }).execute()
                plan_day_id = day_response.data[0]['id']

                tasks = day.get('tasks', [])
                if tasks:
                    task_rows = []
                    for t in tasks:
                        task_rows.append({
                            'plan_day_id': plan_day_id,
                            'course': t.get('course', ''),
                            'task': t.get('task', ''),
                            'duration_minutes': t.get('duration_minutes', 0),
                            'priority': t.get('priority', 'LOW'),
                            'reason': t.get('reason', ''),
                        })
                    client.table('recovery_plan_tasks').insert(task_rows).execute()

        # 7. Insert explanations
        explanations = result.get('explanations', [])
        if explanations:
            exp_rows = []
            for e in explanations:
                exp_rows.append({
                    'analysis_id': analysis_id,
                    'recommendation': e.get('recommendation', ''),
                    'detected_signal': e.get('detected_signal', ''),
                    'why_it_matters': e.get('why_it_matters', ''),
                    'why_this_action': e.get('why_this_action', ''),
                    'expected_result': e.get('expected_result', ''),
                })
            client.table('explanations').insert(exp_rows).execute()

        logger.info(f"Fully persisted analysis {analysis_id} with all child records")
        return analysis_id

    except Exception as e:
        logger.error(f"Failed to persist analysis: {e}", exc_info=True)
        return None
