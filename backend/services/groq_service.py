"""
Groq AI Reasoning Service for ARWA.

Uses Groq's structured output to generate grounded, explainable
academic recovery assessments.

The AI must only reason from data supplied by ARWA.
It must never invent courses, grades, assignments, or deadlines.
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def _get_model():
    return os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b')


SYSTEM_PROMPT = """You are ARWA, an academic risk analyst. You receive structured student data
and deterministic calculations from the ARWA risk engine. Your job:

1. Explain the deterministic values provided to you (do NOT change them).
2. Generate recommendations grounded in the data.
3. Create a recovery plan that respects the strict weekly time budget.
4. Use conditional language for outcomes (may, could, may help) — never guarantee results.

OUTPUT: Return a single JSON object matching the ARWAAssessment schema.
All text fields must be concise (1-2 sentences)."""


GROUNDING_RULES = """
STRICT GROUNDING RULES — VIOLATION = INVALID OUTPUT:

1. DETERMINISTIC VALUES ARE AUTHORITATIVE:
   The academic_risk score/level, burnout_risk score/level, and recovery_score
   are computed by the backend risk engine. You MUST copy these values exactly
   into your response. Do NOT modify, override, or contradict them.
   You may explain WHY these values were computed, but never change the numbers.

2. PRIORITY ORDERING:
   You receive a DETERMINISTIC_PRIORITY list computed from days_remaining,
   estimated_hours, difficulty, and completion status. You MUST use this ordering
   in your "priorities" output. Do NOT independently reorder assignments.

3. EVIDENCE ONLY:
   Every risk factor, recommendation, and explanation must reference a specific
   data point provided (grade, stress, available hours, assignment details).
   Never cite data not in the input.

4. NO INVENTED DATA:
   Do not assume or invent:
   - School policies (probation, suspension, GPA cutoffs, dean's list, late penalties)
   - Commitments or time blocks not in the input
   - Historical trends not in the input
   - External factors not provided
   - Resources (tutoring, office hours, study groups, counseling, writing center)
   - Extensions, incompletes, or special accommodations
   - Specific grade outcomes or pass/fail predictions

5. TIME BUDGET IS WEEKLY:
   available_time is TOTAL hours per WEEK (e.g., 3 hours/week = 180 minutes/week).
   It is NOT hours per day. Never interpret it as a daily budget.
   The recovery plan's total Study minutes across ALL days combined must NOT
   exceed available_time * 60 minutes.

6. WORKLOAD REALITY:
   If total workload exceeds available time, the plan is a TRIAGE/PRIORITIZATION
   plan — not a plan that completes all work. State explicitly:
   - "This is a triage plan — not all assignments can be completed this week."
   - "Remaining workload exceeds available capacity."
   - Identify which work fits within budget and which must be deferred.

7. CONDITIONAL LANGUAGE:
   Never guarantee outcomes. Use: "may help", "could improve", "is expected to".
   Never say: "will raise the grade", "will reduce burnout", "guaranteed to".
   Never predict pass/fail ("should pass", "likely to fail", "will pass").
   Never predict specific grades ("will raise grade to X%").

8. CALCULATIONS ONLY:
   Use arithmetic on input values. No speculation, no "likely", no "probably".
   State facts from the data.

9. COURSES ONLY:
   Recovery plan tasks MUST reference ONLY courses listed in the VALID COURSES
   section. Never invent new courses, assignments, or deadlines.
"""


def _build_user_prompt(risk_signals: Dict[str, Any], student_data: Dict[str, Any]) -> str:
    academic_risk = risk_signals.get('academic_risk', 0.5)
    burnout_risk = risk_signals.get('burnout_risk', 0.5)
    recovery_feasibility = risk_signals.get('recovery_feasibility', 0.5)
    time_budget = risk_signals.get('time_budget', None)
    risk_factors = risk_signals.get('risk_factors', [])

    tasks = student_data.get('tasks', [])
    current_grade = student_data.get('current_grade', 'not provided')
    stress_level = student_data.get('stress_level', 'not provided')
    available_time = student_data.get('available_time', 'not provided')

    total_workload = sum(t.get('estimated_time', 0) for t in tasks)
    available_minutes = int(available_time * 60) if isinstance(available_time, (int, float)) else 0
    workload_exceeds = total_workload > available_time if isinstance(available_time, (int, float)) else False

    # Deterministic priority ordering
    deterministic_priority = _compute_deterministic_priority(tasks)

    task_summary = []
    for t in tasks:
        task_summary.append({
            'name': t.get('name', t.get('title', 'Unnamed')),
            'difficulty': t.get('difficulty', 'unknown'),
            'estimated_hours': t.get('estimated_time', 'unknown'),
            'due_in_hours': t.get('due_in_hours', 'unknown'),
            'missing': t.get('missing', False),
        })

    # Collect valid courses from tasks
    valid_courses = list(set(
        t.get('course', 'Unknown') for t in tasks if t.get('course')
    ))
    valid_names = list(set(
        t.get('name', t.get('title', 'Unknown')) for t in tasks if t.get('name') or t.get('title')
    ))

    prompt = f"""STUDENT DATA:
- Current Grade: {current_grade}
- Stress Level: {stress_level}/10
- Available Study Time: {available_time} hours/week (= {available_minutes} minutes/WEEK, NOT per day)
- Number of Tasks: {len(tasks)}

VALID COURSES (ONLY reference these in your response):
{json.dumps(valid_courses)}

TASKS:
{json.dumps(task_summary, indent=2)}

TIME ANALYSIS:
- Total workload: {total_workload:.1f} hours
- Available time: {available_time} hours/week ({available_minutes} minutes/week)
- Workload vs available: {"EXCEEDS available time — this is a TRIAGE situation" if workload_exceeds else "Fits within available time"}
- Weekly budget: {available_minutes} minutes total for ALL study across the entire week

DETERMINISTIC RISK SCORES (computed by ARWA engine — use these EXACT values):
- Academic Risk: {academic_risk:.2f} ({_score_to_label(academic_risk)}) — score={int(academic_risk * 100)}
- Burnout Risk: {burnout_risk:.2f} ({_score_to_label(burnout_risk)}) — score={int(burnout_risk * 100)}
- Recovery Feasibility: {recovery_feasibility:.2f} — score={int(recovery_feasibility * 100)}

DETERMINISTIC PRIORITY ORDER (computed from deadline urgency, difficulty, completion status):
{_format_deterministic_priority(deterministic_priority)}

RISK FACTORS (ranked by severity):
{_format_risk_factors(risk_factors)}

{GROUNDING_RULES}

ADDITIONAL CONSTRAINTS:
- NEVER invent courses, assignments, or deadlines not listed above.
- NEVER reference tutoring, office hours, study groups, counseling, or any resource not in the input.
- NEVER request extensions, incompletes, or special accommodations not in the input.
- NEVER predict specific grade outcomes (e.g., "will raise grade to X%").
- NEVER make pass/fail predictions (e.g., "should pass", "likely to fail").
- Recovery plan tasks MUST use ONLY the courses listed in VALID COURSES above.
- All "expected_impact" and "expected_result" fields MUST use conditional language ("may help", "could improve").

Produce a complete ARWAAssessment JSON response.
Your "academic_risk", "burnout_risk", and "recovery_score" MUST match the deterministic values above exactly.
Your "priorities" MUST follow the DETERMINISTIC PRIORITY ORDER above.
Your "recovery_plan" total minutes across ALL days must NOT exceed {available_minutes} minutes."""

    return prompt


def _compute_deterministic_priority(tasks: List[Dict]) -> List[Dict]:
    """Compute priority ordering deterministically from task data."""
    scored = []
    for t in tasks:
        due_hrs = t.get('due_in_hours', 168)
        difficulty = t.get('difficulty', 0.5)
        estimated = t.get('estimated_time', 0)
        missing = t.get('missing', False)

        # Urgency: closer deadline = higher score
        if due_hrs <= 24:
            urgency = 1.0
        elif due_hrs <= 48:
            urgency = 0.8
        elif due_hrs <= 72:
            urgency = 0.6
        elif due_hrs <= 120:
            urgency = 0.4
        else:
            urgency = 0.2

        # Missing assignments get a boost
        missing_boost = 0.3 if missing else 0.0

        # Higher difficulty gets slight boost
        difficulty_factor = difficulty * 0.2

        priority_score = urgency * 0.5 + difficulty_factor + missing_boost + 0.1

        if priority_score >= 0.7:
            level = 'CRITICAL'
        elif priority_score >= 0.5:
            level = 'HIGH'
        elif priority_score >= 0.3:
            level = 'MODERATE'
        else:
            level = 'LOW'

        name = t.get('name', t.get('title', 'Unnamed'))
        scored.append({
            'name': name,
            'score': priority_score,
            'level': level,
            'due_in_hours': due_hrs,
            'estimated_hours': estimated,
            'difficulty': difficulty,
        })

    scored.sort(key=lambda x: x['score'], reverse=True)
    for i, s in enumerate(scored):
        s['rank'] = i + 1

    return scored


def _format_deterministic_priority(priority: List[Dict]) -> str:
    if not priority:
        return "No tasks."
    lines = []
    for p in priority:
        lines.append(
            f"{p['rank']}. {p['name']} [{p['level']}]: "
            f"due_in={p['due_in_hours']}h, est={p['estimated_hours']}h, "
            f"difficulty={p['difficulty']}"
        )
    return '\n'.join(lines)


def _score_to_label(score: float) -> str:
    if score >= 0.8:
        return 'CRITICAL'
    elif score >= 0.6:
        return 'HIGH'
    elif score >= 0.4:
        return 'MODERATE'
    return 'LOW'


def _format_risk_factors(factors):
    if not factors:
        return "No risk factors computed."
    lines = []
    for i, f in enumerate(factors, 1):
        lines.append(f"{i}. {f.get('factor', 'Unknown')} [{f.get('severity', 'LOW')}]: {f.get('evidence', 'No evidence')}")
    return '\n'.join(lines)


def _get_arwa_assessment_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "academic_risk": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "level": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "CRITICAL"]},
                    "explanation": {"type": "string"},
                },
                "required": ["score", "level", "explanation"],
            },
            "burnout_risk": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "level": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "CRITICAL"]},
                    "explanation": {"type": "string"},
                },
                "required": ["score", "level", "explanation"],
            },
            "recovery_score": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "explanation": {"type": "string"},
                },
                "required": ["score", "explanation"],
            },
            "overall_summary": {"type": "string"},
            "risk_factors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "factor": {"type": "string"},
                        "severity": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "CRITICAL"]},
                        "impact": {"type": "integer", "minimum": 0, "maximum": 100},
                        "evidence": {"type": "string"},
                        "explanation": {"type": "string"},
                    },
                    "required": ["factor", "severity", "impact", "evidence", "explanation"],
                },
            },
            "priorities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "rank": {"type": "integer", "minimum": 1},
                        "course_or_task": {"type": "string"},
                        "priority": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "CRITICAL"]},
                        "reason": {"type": "string"},
                    },
                    "required": ["rank", "course_or_task", "priority", "reason"],
                },
            },
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "action": {"type": "string"},
                        "reason": {"type": "string"},
                        "priority": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "CRITICAL"]},
                        "expected_impact": {"type": "string"},
                    },
                    "required": ["action", "reason", "priority", "expected_impact"],
                },
            },
            "recovery_plan": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "date": {"type": "string"},
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "course": {"type": "string"},
                                    "task": {"type": "string"},
                                    "duration_minutes": {"type": "integer", "minimum": 0},
                                    "priority": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "CRITICAL"]},
                                    "reason": {"type": "string"},
                                },
                                "required": ["course", "task", "duration_minutes", "priority", "reason"],
                            },
                        },
                        "total_study_minutes": {"type": "integer", "minimum": 0},
                    },
                    "required": ["date", "tasks", "total_study_minutes"],
                },
            },
            "explanations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "recommendation": {"type": "string"},
                        "detected_signal": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                        "why_this_action": {"type": "string"},
                        "expected_result": {"type": "string"},
                    },
                    "required": ["recommendation", "detected_signal", "why_it_matters", "why_this_action", "expected_result"],
                },
            },
        },
        "required": [
            "academic_risk", "burnout_risk", "recovery_score",
            "overall_summary", "risk_factors", "priorities",
            "recommendations", "recovery_plan", "explanations",
        ],
    }


def _repair_json(raw: str) -> Optional[Dict[str, Any]]:
    """Attempt to repair common JSON issues from Groq responses."""
    if not raw:
        return None

    cleaned = raw.strip()
    cleaned = cleaned.replace('\\n', ' ')
    cleaned = cleaned.replace('\u2013', '-').replace('\u2014', '-')
    cleaned = cleaned.replace('\u201c', '"').replace('\u201d', '"')
    cleaned = cleaned.replace('\u2018', "'").replace('\u2019', "'")

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    open_braces = cleaned.count('{') - cleaned.count('}')
    open_brackets = cleaned.count('[') - cleaned.count(']')
    if open_braces > 0 or open_brackets > 0:
        try:
            return json.loads(cleaned + ']' * open_brackets + '}' * open_braces)
        except json.JSONDecodeError:
            pass

    cleaned2 = re.sub(r',\s*([}\]])', r'\1', cleaned)
    try:
        return json.loads(cleaned2)
    except json.JSONDecodeError:
        pass

    cleaned3 = cleaned2.replace('"problem":', '"task":')
    try:
        return json.loads(cleaned3)
    except json.JSONDecodeError:
        pass

    logger.error("JSON repair failed")
    return None


def _validate_recovery_plan(assessment: Dict[str, Any], student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and enforce weekly budget on recovery plan."""
    available_time = student_data.get('available_time', 4)
    available_minutes = int(available_time * 60) if isinstance(available_time, (int, float)) else 180

    plan = assessment.get('recovery_plan', [])
    if not plan:
        return assessment

    today = datetime.now().date()

    # 1. Remove impossible dates (before today)
    cleaned_plan = []
    for day in plan:
        try:
            day_date = datetime.strptime(day.get('date', ''), '%Y-%m-%d').date()
            if day_date >= today:
                cleaned_plan.append(day)
        except (ValueError, TypeError):
            cleaned_plan.append(day)

    # 2. Remove tasks with negative or zero durations
    for day in cleaned_plan:
        tasks = day.get('tasks', [])
        day['tasks'] = [t for t in tasks if t.get('duration_minutes', 0) > 0]

    # 3. Remove days with no tasks
    cleaned_plan = [d for d in cleaned_plan if d.get('tasks')]

    # 4. Enforce weekly budget: sum of all days must not exceed available_minutes
    total_planned = sum(d.get('total_study_minutes', 0) for d in cleaned_plan)
    if total_planned > available_minutes:
        # Scale down proportionally
        scale = available_minutes / max(total_planned, 1)
        remaining = available_minutes
        for day in cleaned_plan:
            day_total = day.get('total_study_minutes', 0)
            new_day_total = min(int(day_total * scale), remaining)
            if new_day_total <= 0:
                day['tasks'] = []
                day['total_study_minutes'] = 0
                continue

            day_tasks = day.get('tasks', [])
            task_scale = new_day_total / max(day_total, 1)
            new_tasks = []
            day_remaining = new_day_total
            for t in day_tasks:
                old_min = t.get('duration_minutes', 0)
                new_min = max(5, int(old_min * task_scale)) if old_min > 0 else 0
                new_min = min(new_min, day_remaining)
                if new_min > 0:
                    t['duration_minutes'] = new_min
                    day_remaining -= new_min
                    new_tasks.append(t)
            day['tasks'] = new_tasks
            day['total_study_minutes'] = sum(t['duration_minutes'] for t in new_tasks)
            remaining -= day['total_study_minutes']

    # 5. Recalculate total_study_minutes to be consistent
    for day in cleaned_plan:
        day['total_study_minutes'] = sum(t.get('duration_minutes', 0) for t in day.get('tasks', []))

    # 6. Validate risk score consistency
    for field in ['academic_risk', 'burnout_risk']:
        risk_obj = assessment.get(field, {})
        if isinstance(risk_obj, dict):
            score = risk_obj.get('score', 50)
            level = risk_obj.get('level', 'MODERATE')
            expected_level = _score_to_label(score / 100)
            if level != expected_level:
                logger.warning(f"AI {field} level mismatch: score={score} but level={level}. Correcting to {expected_level}.")
                risk_obj['level'] = expected_level

    assessment['recovery_plan'] = cleaned_plan
    return assessment


async def call_groq(risk_signals: Dict[str, Any], student_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Call Groq API for AI-powered reasoning.
    Returns parsed assessment or None if Groq is unavailable.
    """
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        logger.warning("GROQ_API_KEY not set. AI reasoning unavailable.")
        return None
    logger.info(f"GROQ_API_KEY present: len={len(api_key)}")

    try:
        import groq
    except ImportError:
        logger.warning("groq package not installed. AI reasoning unavailable.")
        return None

    user_prompt = _build_user_prompt(risk_signals, student_data)
    content = None

    try:
        client = groq.Groq(api_key=api_key)

        model = _get_model()
        logger.info(f"Calling Groq model={model}")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "arwa_assessment",
                    "strict": True,
                    "schema": _get_arwa_assessment_schema(),
                },
            },
        )

        logger.info(f"Groq response received, status=ok, choices={len(response.choices)}")
        content = response.choices[0].message.content
        if not content:
            logger.error("Empty response from Groq")
            return None

        assessment = json.loads(content)
        logger.info(f"Groq assessment parsed, keys={list(assessment.keys())}")

        return assessment

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq response as JSON: {e}")
        repaired = _repair_json(content or "")
        if repaired:
            logger.info("Repaired JSON successfully")
            return repaired
        return None
    except Exception as e:
        logger.error(f"Groq API call failed: {type(e).__name__}: {e}", exc_info=True)
        return None
