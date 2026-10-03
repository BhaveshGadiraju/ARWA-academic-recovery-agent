"""
ARWA Analysis Service.

Central orchestration layer that:
1. Validates input
2. Computes deterministic risk signals
3. Calls Groq for AI reasoning
4. Overrides AI values with deterministic authoritative values
5. Validates and sanitizes AI output
6. Falls back to deterministic assessment if Groq fails
"""

import re
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from backend.services.risk_engine import RiskEngine
from backend.services.groq_service import call_groq, _validate_recovery_plan, _compute_deterministic_priority

logger = logging.getLogger(__name__)

# Patterns that indicate the AI hallucinated or made unsupported claims
_HALLUCINATION_PATTERNS = [
    # ── Invented commitments or time blocks ──────────────────────────────
    (r'committed\s+(time|minutes|hours)', 'time already committed'),
    (r'existing\s+commitments?', 'existing commitments'),
    (r'already[- ]committed', 'already committed'),
    (r'other\s+obligations?', 'other obligations'),
    (r'600\s+minutes', 'specific invented time block'),
    (r'prior\s+commitments?', 'prior commitments'),
    # ── Invented school policies ─────────────────────────────────────────
    (r'academic\s+probation', 'academic probation policy'),
    (r'academic\s+dismissal', 'academic dismissal policy'),
    (r'academic\s+warning', 'academic warning policy'),
    (r'suspension', 'suspension policy'),
    (r'expulsion', 'expulsion policy'),
    (r'gpa\s+cutoff', 'GPA cutoff policy'),
    (r'dean.s\s+list', "dean's list policy"),
    (r'fail\s+out', 'failure policy'),
    (r'flunk', 'failure policy'),
    (r'late\s+penalty', 'late penalty policy'),
    (r'deduction\s+for\s+late', 'late penalty policy'),
    (r'grade\s+penalty', 'grade penalty policy'),
    (r'academic\s+standing', 'academic standing policy'),
    (r'academic\s+probation', 'academic probation policy'),
    # ── Invented resources or support ─────────────────────────────────────
    (r'tutor(ing)?', 'invented tutoring resource'),
    (r'office\s+hours', 'invented office hours'),
    (r'study\s+group', 'invented study group'),
    (r'counsel(ing|or)', 'invented counseling resource'),
    (r'mental\s+health', 'invented mental health resource'),
    (r'writing\s+center', 'invented writing center'),
    (r'academic\s+advisor', 'invented advisor'),
    (r'syllabus', 'invented syllabus context'),
    (r'grading\s+rubric', 'invented rubric context'),
    # ── Invented policies about extensions or incompletes ─────────────────
    (r'request\s+an?\s+extension', 'invented extension policy'),
    (r'ask\s+for\s+an?\s+extension', 'invented extension policy'),
    (r'file\s+for\s+incomplete', 'invented incomplete policy'),
    (r'late\s+submission', 'invented late submission policy'),
    # ── Claims that contradict available_time being positive ──────────────
    (r'no\s+(study\s+)?time\s+(remains|left|remaining)', 'claim of no study time'),
    (r'zero\s+time\s+(available|remaining)', 'claim of zero time'),
    (r'unavailable\s+for\s+studying', 'claim of unavailable time'),
    # ── Guaranteed outcome claims (should be conditional) ────────────────
    (r'will\s+(raise|improve|increase|boost)\s+the\s+grade', 'guaranteed grade improvement'),
    (r'will\s+(reduce|lower|decrease)\s+burnout', 'guaranteed burnout reduction'),
    (r'will\s+ensure', 'guaranteed outcome'),
    (r'will\s+guarantee', 'guaranteed outcome'),
    (r'guaranteed\s+to', 'guaranteed outcome'),
    (r'definitely\s+(will|help|improve|raise|lower)', 'definite outcome claim'),
    (r'certainly\s+(will|help|improve|raise|lower)', 'certain outcome claim'),
    (r'will\s+definitely', 'definite outcome claim'),
    (r'will\s+certainly', 'certain outcome claim'),
    (r'will\s+pass', 'guaranteed pass claim'),
    (r'will\s+fail', 'guaranteed fail claim'),
    (r'should\s+pass', 'predicted pass claim'),
    (r'likely\s+to\s+pass', 'predicted pass claim'),
    (r'expected\s+to\s+pass', 'predicted pass claim'),
    (r'will\s+raise\s+grade\s+to\s+\d', 'specific grade prediction'),
    (r'grade\s+will\s+(be|reach)\s+\d', 'specific grade prediction'),
    # ── Unsupported grade claims ──────────────────────────────────────────
    (r'adds\s+earned\s+points?\s+and\s+raises?\s+the\s+grade', 'unsupported grade claim'),
    (r'finishing\s+assignments?\s+adds?\s+earned', 'unsupported grade claim'),
    (r'burnout\s+impairs?\s+health', 'unsupported health claim'),
    (r'leads?\s+to\s+(burnout|depression|anxiety)', 'unsupported health claim'),
    (r'causes?\s+(burnout|depression|anxiety)', 'unsupported health claim'),
    # ── False completeness claims ─────────────────────────────────────────
    (r'all\s+assignments?\s+(can|will)\s+be\s+completed', 'false completeness claim'),
    (r'(will|can|able to)\s+complete\s+all\s+(assignments?|tasks?|work)', 'false completeness claim'),
    (r'complete\s+all\s+(assignments?|tasks?|work)', 'false completeness claim'),
    (r'finish\s+all\s+(assignments?|tasks?|work)', 'false completeness claim'),
]


class AnalysisService:
    """
    Orchestrates the full ARWA analysis pipeline.
    Deterministic risk engine + Groq AI reasoning + fallback.
    """

    def __init__(self):
        self.risk_engine = RiskEngine()

    async def analyze(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        tasks = student_data.get('tasks', [])
        if not tasks:
            student_data['tasks'] = []

        risk_signals = self.risk_engine.compute_all_signals(student_data)

        ai_assessment = await call_groq(risk_signals, student_data)

        if ai_assessment:
            ai_assessment = self._enforce_deterministic_authority(ai_assessment, risk_signals, student_data)
            ai_assessment = self._sanitize_ai_output(ai_assessment, student_data)
            ai_assessment = _validate_recovery_plan(ai_assessment, student_data)
            if 'recovery_plan' in ai_assessment:
                ai_assessment['recovery_plan'] = self._validate_recovery_plan_courses(
                    ai_assessment['recovery_plan'], student_data
                )
            ai_assessment['ai_powered'] = True
            ai_assessment['fallback_used'] = False
        else:
            ai_assessment = self._build_deterministic_assessment(risk_signals, student_data)
            ai_assessment['ai_powered'] = False
            ai_assessment['fallback_used'] = True

        return ai_assessment

    def _enforce_deterministic_authority(
        self, ai_assessment: Dict, risk_signals: Dict, student_data: Dict
    ) -> Dict[str, Any]:
        """Override AI values with deterministic authoritative values."""
        academic_risk = risk_signals.get('academic_risk', 0.5)
        burnout_risk = risk_signals.get('burnout_risk', 0.5)
        recovery_feasibility = risk_signals.get('recovery_feasibility', 0.5)
        tasks = student_data.get('tasks', [])

        # ALWAYS override risk scores and levels — deterministic is authoritative
        ai_assessment['academic_risk'] = {
            'score': int(academic_risk * 100),
            'level': self._score_to_level(academic_risk),
            'explanation': ai_assessment.get('academic_risk', {}).get('explanation',
                f"Risk computed from grade={student_data.get('current_grade', 'N/A')}%, "
                f"missing tasks={sum(1 for t in tasks if t.get('missing', False))}"),
        }

        ai_assessment['burnout_risk'] = {
            'score': int(burnout_risk * 100),
            'level': self._score_to_level(burnout_risk),
            'explanation': ai_assessment.get('burnout_risk', {}).get('explanation',
                f"Burnout risk from stress={student_data.get('stress_level', 'N/A')}/10, "
                f"available time={student_data.get('available_time', 'N/A')} hrs/week"),
        }

        ai_assessment['recovery_score'] = {
            'score': int(recovery_feasibility * 100),
            'explanation': ai_assessment.get('recovery_score', {}).get('explanation',
                'Recovery feasibility based on available time and risk levels.'),
        }

        # Override priorities with deterministic ordering
        deterministic_priority = _compute_deterministic_priority(tasks)
        ai_assessment['priorities'] = [
            {
                'rank': p['rank'],
                'course_or_task': p['name'],
                'priority': p['level'],
                'reason': f"Due in {p['due_in_hours']}h, est. {p['estimated_hours']}h, difficulty {p['difficulty']}",
            }
            for p in deterministic_priority
        ]

        # Override risk_factors severity and impact with deterministic values
        # These are computed from signal scores, not AI judgment
        if 'risk_factors' in ai_assessment:
            for rf in ai_assessment['risk_factors']:
                # Ensure evidence references actual input data
                evidence = rf.get('evidence', '')
                if not self._evidence_references_input(evidence, student_data):
                    # Replace with grounded evidence
                    rf['evidence'] = f"Data: grade={student_data.get('current_grade', 'N/A')}%, stress={student_data.get('stress_level', 'N/A')}/10, available_time={student_data.get('available_time', 'N/A')} hrs/week"

        return ai_assessment

    def _sanitize_ai_output(self, ai_assessment: Dict, student_data: Dict) -> Dict:
        """Scan AI output for hallucinated claims and sanitize them."""
        available_time = student_data.get('available_time', 4)
        tasks = student_data.get('tasks', [])
        total_workload = sum(t.get('estimated_time', 0) for t in tasks)
        text_fields = self._collect_text_fields(ai_assessment)
        violations = []

        for path, text in text_fields:
            for pattern, label in _HALLUCINATION_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    violations.append((path, label, text))

        if violations:
            logger.warning(f"AI hallucination detected in {len(violations)} field(s): {[v[1] for v in violations]}")
            ai_assessment = self._rewrite_violations(ai_assessment, violations, student_data)

        # Ensure overall_summary reflects triage if needed
        if 'overall_summary' in ai_assessment:
            summary = ai_assessment['overall_summary']
            workload_exceeds = total_workload > available_time if isinstance(available_time, (int, float)) else False
            if workload_exceeds:
                if not re.search(r'triage|prioritiz|exceeds|capacity|defer', summary, re.IGNORECASE):
                    ai_assessment['overall_summary'] = (
                        f"Grade: {student_data.get('current_grade', 'N/A')}%. "
                        f"Workload ({total_workload:.1f}h) exceeds available time ({available_time}h/week). "
                        f"This is a triage plan — not all assignments can be completed this week."
                    )

        # Ensure risk_factors don't contain unsupported claims
        for rf in ai_assessment.get('risk_factors', []):
            for field in ['explanation', 'evidence']:
                text = rf.get(field, '')
                if text and re.search(r'(burnout\s+impairs?|leads?\s+to|causes?)\s+(burnout|depression|anxiety|health)', text, re.IGNORECASE):
                    rf[field] = f"Based on provided data (grade={student_data.get('current_grade', 'N/A')}%, stress={student_data.get('stress_level', 'N/A')}/10)."

        # Ensure explanations don't guarantee outcomes
        for explanation in ai_assessment.get('explanations', []):
            for field in ['expected_result', 'why_this_action']:
                text = explanation.get(field, '')
                if text and re.search(r'will\s+(definitely|certainly|guarantee|ensure|raise|improve|lower|reduce|pass|fail)', text, re.IGNORECASE):
                    explanation[field] = f"May help improve outcomes given current constraints."

        # Ensure recommendations don't guarantee outcomes
        for rec in ai_assessment.get('recommendations', []):
            impact = rec.get('expected_impact', '')
            if impact and re.search(r'will\s+(definitely|certainly|guarantee|ensure|raise|improve|lower|reduce|pass|fail)', impact, re.IGNORECASE):
                rec['expected_impact'] = f"May help improve outcomes given current constraints."

        return ai_assessment

    def _collect_text_fields(self, obj: Any, path: str = "") -> List[tuple]:
        """Recursively collect all string values with their JSON paths."""
        results = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                results.extend(self._collect_text_fields(v, f"{path}.{k}"))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                results.extend(self._collect_text_fields(v, f"{path}[{i}]"))
        elif isinstance(obj, str):
            results.append((path, obj))
        return results

    def _rewrite_violations(self, ai_assessment: Dict, violations: List, student_data: Dict) -> Dict:
        """Replace hallucinated text with grounded alternatives."""
        grade = student_data.get('current_grade', 'unknown')
        stress = student_data.get('stress_level', 'unknown')
        available = student_data.get('available_time', 'unknown')
        tasks = student_data.get('tasks', [])
        total_workload = sum(t.get('estimated_time', 0) for t in tasks)

        for path, label, original in violations:
            parts = path.split('.')
            key = parts[-1] if parts else path

            if 'summary' in key.lower():
                grounded = (
                    f"Grade: {grade}%. "
                    f"Workload ({total_workload:.1f}h) exceeds {available}h/week available. "
                    f"Stress: {stress}/10. Triage and prioritization required."
                )
            elif 'explanation' in key.lower():
                grounded = f"Based on grade ({grade}%), stress ({stress}/10), and {available}h/week available."
            elif 'evidence' in key.lower():
                grounded = f"Data: grade={grade}%, stress={stress}/10, available_time={available} hrs/week"
            elif 'reason' in key.lower():
                grounded = f"Based on data: grade={grade}%, workload={total_workload:.1f}h, available={available}h/week"
            elif 'expected_impact' in key.lower():
                grounded = f"May help improve outcomes given current constraints."
            else:
                grounded = f"Analysis based on provided data (grade: {grade}%, stress: {stress}/10, time: {available}h/week)."

            self._set_nested(ai_assessment, parts[1:], grounded)
            logger.info(f"Sanitized {path}: replaced '{label}' with grounded text")

        return ai_assessment

    def _set_nested(self, obj: Dict, keys: List[str], value: str):
        """Set a value in a nested dict using a list of keys."""
        for k in keys[:-1]:
            if k.isdigit():
                obj = obj[int(k)]
            else:
                obj = obj.setdefault(k, {})
        final_key = keys[-1]
        if final_key.isdigit():
            obj[int(final_key)] = value
        else:
            obj[final_key] = value

    def _evidence_references_input(self, evidence: str, student_data: Dict) -> bool:
        """Check if evidence text references actual input data points.
        Uses word boundary matching for all numeric values to avoid
        false positives (e.g., "2" matching inside "2.0" or "200").
        Excludes decimal numbers (e.g., "2.0" should not match integer 2).
        """
        evidence_lower = evidence.lower()

        def _has_number(value, text):
            """Check if a number appears as a standalone integer in text.
            Matches '5' but not '5.0' or '50' or '5.5'.
            """
            val_str = str(int(value)) if isinstance(value, float) and value == int(value) else str(value)
            # Match the number but NOT if preceded/followed by a digit or dot
            return bool(re.search(r'(?<![.\d])' + re.escape(val_str) + r'(?![.\d])', text))

        # Evidence should reference at least one actual input value
        has_grade = _has_number(student_data.get('current_grade', ''), evidence)
        has_stress = _has_number(student_data.get('stress_level', ''), evidence)
        has_time = _has_number(student_data.get('available_time', ''), evidence)
        has_workload = any(
            _has_number(t.get('estimated_time', 0), evidence)
            for t in student_data.get('tasks', [])
        )
        # Also check for total workload (sum of all task times)
        total_workload = sum(t.get('estimated_time', 0) for t in student_data.get('tasks', []))
        has_total_workload = _has_number(total_workload, evidence) if total_workload > 0 else False
        # Use word boundary matching for courses, but require at least 2 chars
        # to avoid false positives with single-letter courses matching articles
        has_course = any(
            re.search(r'\b' + re.escape(t.get('course', '').lower()) + r'\b', evidence_lower)
            for t in student_data.get('tasks', [])
            if t.get('course') and len(t.get('course', '')) >= 2
        )
        # At least one concrete data point must be referenced
        return has_grade or has_stress or has_time or has_workload or has_total_workload or has_course

    def _validate_recovery_plan_courses(self, plan: List[Dict], student_data: Dict) -> List[Dict]:
        """Ensure recovery plan tasks only reference courses in the input."""
        valid_courses = set()
        for t in student_data.get('tasks', []):
            course = t.get('course', '').strip()
            name = t.get('name', t.get('title', '')).strip()
            if course:
                valid_courses.add(course.lower())
            if name:
                valid_courses.add(name.lower())

        for day in plan:
            validated_tasks = []
            for task in day.get('tasks', []):
                course = task.get('course', '').strip()
                if course.lower() in valid_courses:
                    validated_tasks.append(task)
                else:
                    # Replace invented course with nearest valid course
                    task['course'] = next(iter(valid_courses), 'General Study')
                    validated_tasks.append(task)
            day['tasks'] = validated_tasks
            day['total_study_minutes'] = sum(t.get('duration_minutes', 0) for t in day['tasks'])

        return [d for d in plan if d.get('tasks')]

    def _build_deterministic_assessment(
        self, risk_signals: Dict, student_data: Dict
    ) -> Dict[str, Any]:
        academic_risk = risk_signals.get('academic_risk', 0.5)
        burnout_risk = risk_signals.get('burnout_risk', 0.5)
        recovery_feasibility = risk_signals.get('recovery_feasibility', 0.5)
        risk_factors = risk_signals.get('risk_factors', [])
        time_budget = risk_signals.get('time_budget')

        tasks = student_data.get('tasks', [])
        available_minutes = time_budget.total_available_minutes if time_budget else int(student_data.get('available_time', 4) * 60)
        total_workload = sum(t.get('estimated_time', 0) for t in tasks)
        workload_exceeds = total_workload > student_data.get('available_time', 4)

        priorities = self._build_priorities(tasks, risk_signals)
        recommendations = self._build_recommendations(risk_signals, student_data, tasks)
        recovery_plan = self._build_recovery_plan(tasks, available_minutes, priorities, workload_exceeds)
        explanations = self._build_explanations(risk_signals, recommendations, student_data)

        return {
            'academic_risk': {
                'score': int(academic_risk * 100),
                'level': self._score_to_level(academic_risk),
                'explanation': self._explain_academic_risk(student_data, risk_signals),
            },
            'burnout_risk': {
                'score': int(burnout_risk * 100),
                'level': self._score_to_level(burnout_risk),
                'explanation': self._explain_burnout_risk(student_data, risk_signals),
            },
            'recovery_score': {
                'score': int(recovery_feasibility * 100),
                'explanation': self._explain_recovery(recovery_feasibility, time_budget),
            },
            'overall_summary': self._build_summary(academic_risk, burnout_risk, student_data, workload_exceeds, total_workload),
            'risk_factors': risk_factors,
            'priorities': priorities,
            'recommendations': recommendations,
            'recovery_plan': recovery_plan,
            'explanations': explanations,
        }

    def _explain_academic_risk(self, student_data, risk_signals) -> str:
        grade = student_data.get('current_grade', 'unknown')
        tasks = student_data.get('tasks', [])
        missing = sum(1 for t in tasks if t.get('missing', False))
        parts = [f"Current grade: {grade}%."]
        if missing > 0:
            parts.append(f"{missing} incomplete assignment(s).")
        academic = risk_signals.get('academic_risk', 0.5)
        if academic >= 0.6:
            parts.append("Academic risk is elevated and requires immediate attention.")
        elif academic >= 0.4:
            parts.append("Academic risk is moderate.")
        else:
            parts.append("Academic risk is currently manageable.")
        return ' '.join(parts)

    def _explain_burnout_risk(self, student_data, risk_signals) -> str:
        stress = student_data.get('stress_level', 'unknown')
        available = student_data.get('available_time', 'unknown')
        burnout = risk_signals.get('burnout_risk', 0.5)
        parts = [f"Stress level: {stress}/10."]
        parts.append(f"Available study time: {available} hours/week.")
        if burnout >= 0.6:
            parts.append("Burnout risk is high. Regular breaks and workload reduction may help.")
        elif burnout >= 0.4:
            parts.append("Burnout risk is moderate. Monitor stress levels.")
        else:
            parts.append("Burnout risk is currently low.")
        return ' '.join(parts)

    def _explain_recovery(self, feasibility, time_budget) -> str:
        pct = int(feasibility * 100)
        if time_budget and time_budget.remaining_minutes < 0:
            return f"Recovery feasibility: {pct}%. Workload exceeds available time. Some tasks may need to be deferred."
        elif feasibility >= 0.7:
            return f"Recovery feasibility: {pct}%. Current situation may be recoverable with focused effort."
        elif feasibility >= 0.4:
            return f"Recovery feasibility: {pct}%. Recovery is possible but will require prioritization."
        return f"Recovery feasibility: {pct}%. Significant challenges to recovery exist."

    def _build_summary(self, academic_risk, burnout_risk, student_data, workload_exceeds=False, total_workload=0) -> str:
        grade = student_data.get('current_grade', 'unknown')
        stress = student_data.get('stress_level', 'unknown')
        available = student_data.get('available_time', 'unknown')
        parts = [f"Grade: {grade}%. Stress: {stress}/10."]
        if academic_risk >= 0.6:
            parts.append("Academic risk is HIGH.")
        elif academic_risk >= 0.4:
            parts.append("Academic risk is MODERATE.")
        else:
            parts.append("Academic risk is LOW.")
        if burnout_risk >= 0.6:
            parts.append("Burnout risk is HIGH.")
        elif burnout_risk >= 0.4:
            parts.append("Burnout risk is MODERATE.")
        else:
            parts.append("Burnout risk is LOW.")
        if workload_exceeds:
            parts.append(f"Workload ({total_workload:.1f}h) exceeds available time ({available}h/week). This is a triage plan.")
        return ' '.join(parts)

    def _build_priorities(self, tasks, risk_signals) -> list:
        scored = []
        for t in tasks:
            urgency = 1.0
            due = t.get('due_in_hours', 168)
            if due <= 24:
                urgency = 1.0
            elif due <= 48:
                urgency = 0.8
            elif due <= 72:
                urgency = 0.6
            elif due <= 120:
                urgency = 0.4
            else:
                urgency = 0.3

            difficulty = t.get('difficulty', 0.5)
            missing = 1.0 if t.get('missing', False) else 0.0

            priority_score = urgency * 0.5 + difficulty * 0.2 + missing * 0.3
            scored.append((t, priority_score))

        scored.sort(key=lambda x: x[1], reverse=True)

        priorities = []
        for rank, (task, score) in enumerate(scored[:6], 1):
            if score >= 0.7:
                level = 'CRITICAL'
            elif score >= 0.5:
                level = 'HIGH'
            elif score >= 0.3:
                level = 'MODERATE'
            else:
                level = 'LOW'

            name = task.get('name', task.get('title', 'Unnamed task'))
            due_hrs = task.get('due_in_hours', 'unknown')
            priorities.append({
                'rank': rank,
                'course_or_task': name,
                'priority': level,
                'reason': f"Due in {due_hrs} hours, difficulty {task.get('difficulty', 'N/A')}",
            })

        return priorities

    def _build_recommendations(self, risk_signals, student_data, tasks) -> list:
        recommendations = []
        academic_risk = risk_signals.get('academic_risk', 0.5)
        burnout_risk = risk_signals.get('burnout_risk', 0.5)
        available = student_data.get('available_time', 4)
        total_workload = sum(t.get('estimated_time', 0) for t in tasks)
        workload_exceeds = total_workload > available if isinstance(available, (int, float)) else False

        if workload_exceeds:
            recommendations.append({
                'action': f"Triage workload: {total_workload:.1f}h needed but only {available}h/week available",
                'reason': f"Total estimated workload ({total_workload:.1f}h) exceeds available time ({available}h/week)",
                'priority': 'CRITICAL',
                'expected_impact': 'Realistic allocation of limited study time to highest-priority tasks',
            })

        if burnout_risk >= 0.6:
            recommendations.append({
                'action': 'Schedule 15-minute breaks between study sessions',
                'reason': f"Burnout risk is {self._score_to_level(burnout_risk)}",
                'priority': 'HIGH',
                'expected_impact': 'May help reduce burnout risk and improve focus',
            })

        if academic_risk >= 0.6 and tasks:
            recommendations.append({
                'action': 'Use Pomodoro technique (25 min study, 5 min break)',
                'reason': 'High academic risk requires focused, efficient study sessions',
                'priority': 'HIGH',
                'expected_impact': 'May help improve retention and reduce study fatigue',
            })

        if not recommendations:
            recommendations.append({
                'action': 'Continue current study plan',
                'reason': 'Risk levels are manageable',
                'priority': 'LOW',
                'expected_impact': 'May help maintain current progress',
            })

        return recommendations

    def _build_recovery_plan(self, tasks, available_minutes, priorities, workload_exceeds=False) -> list:
        plan = []
        today = datetime.now().date()
        remaining_minutes = available_minutes

        day_tasks = []
        for p in priorities[:4]:
            task_name = p.get('course_or_task', 'Study')
            priority_level = p.get('priority', 'MODERATE')

            if priority_level == 'CRITICAL':
                minutes = min(45, remaining_minutes)
            elif priority_level == 'HIGH':
                minutes = min(30, remaining_minutes)
            else:
                minutes = min(20, remaining_minutes)

            if minutes > 0:
                day_tasks.append({
                    'course': task_name,
                    'task': f"Focus on {task_name}" + (" [TRIAGE]" if workload_exceeds else ""),
                    'duration_minutes': minutes,
                    'priority': priority_level,
                    'reason': f"Priority {p.get('rank', '?')}: {p.get('reason', '')}",
                })
                remaining_minutes -= minutes

        if day_tasks:
            plan.append({
                'date': today.isoformat(),
                'tasks': day_tasks,
                'total_study_minutes': sum(t['duration_minutes'] for t in day_tasks),
            })

        return plan

    def _build_explanations(self, risk_signals, recommendations, student_data) -> list:
        explanations = []
        risk_factors = risk_signals.get('risk_factors', [])

        for factor in risk_factors[:3]:
            explanations.append({
                'recommendation': f"Address {factor.get('factor', 'risk factor')}",
                'detected_signal': factor.get('evidence', 'Data signal detected'),
                'why_it_matters': factor.get('explanation', 'This factor affects academic outcomes'),
                'why_this_action': f"Addressing {factor.get('factor', 'this factor')} may help reduce overall risk",
                'expected_result': f"May help improve {factor.get('factor', 'metric')} and lower risk score",
            })

        for rec in recommendations[:2]:
            explanations.append({
                'recommendation': rec.get('action', ''),
                'detected_signal': rec.get('reason', ''),
                'why_it_matters': rec.get('reason', ''),
                'why_this_action': rec.get('reason', ''),
                'expected_result': rec.get('expected_impact', ''),
            })

        return explanations

    def _score_to_level(self, score: float) -> str:
        if score >= 0.8:
            return 'CRITICAL'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MODERATE'
        return 'LOW'
