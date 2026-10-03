"""
Adversarial Hallucination Tests for ARWA.

Tests that the sanitization layer catches and rewrites specific
hallucination patterns. Each test injects a known hallucination
into AI output and verifies it is caught or rewritten.
"""

import re
import os
import sys
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from backend.services.analysis_service import AnalysisService, _HALLUCINATION_PATTERNS


# ── Test data ───────────────────────────────────────────────────────────────

BASE_STUDENT_DATA = {
    'current_grade': 72,
    'stress_level': 7,
    'available_time': 3,
    'tasks': [
        {
            'name': 'Calculus',
            'title': 'Calculus',
            'course': 'Mathematics',
            'difficulty': 0.6,
            'estimated_time': 2,
            'due_in_hours': 72,
            'missing': False,
        },
        {
            'name': 'Physics',
            'title': 'Physics',
            'course': 'Physics',
            'difficulty': 0.7,
            'estimated_time': 3,
            'due_in_hours': 96,
            'missing': False,
        },
    ],
}

BASE_AI_ASSESSMENT = {
    'academic_risk': {'score': 23, 'level': 'LOW', 'explanation': 'Grade is 72%.'},
    'burnout_risk': {'score': 77, 'level': 'HIGH', 'explanation': 'Stress is 7/10.'},
    'recovery_score': {'score': 29, 'explanation': 'Recovery feasibility is 29%.'},
    'overall_summary': 'Grade: 72%. Stress: 7/10. Workload exceeds available time.',
    'risk_factors': [
        {'factor': 'Workload', 'severity': 'HIGH', 'impact': 80, 'evidence': '10h workload', 'explanation': 'Heavy workload.'},
    ],
    'priorities': [
        {'rank': 1, 'course_or_task': 'Calculus', 'priority': 'HIGH', 'reason': 'Due in 72h.'},
    ],
    'recommendations': [
        {'action': 'Focus on Calculus', 'reason': 'Urgent deadline', 'priority': 'HIGH', 'expected_impact': 'May help.'},
    ],
    'recovery_plan': [
        {
            'date': '2026-08-12',
            'tasks': [
                {'course': 'Mathematics', 'task': 'Study Calculus', 'duration_minutes': 60, 'priority': 'HIGH', 'reason': 'Urgent.'},
            ],
            'total_study_minutes': 60,
        },
    ],
    'explanations': [
        {
            'recommendation': 'Focus on Calculus',
            'detected_signal': 'Urgent deadline',
            'why_it_matters': 'Grade is 72%.',
            'why_this_action': 'May help improve.',
            'expected_result': 'May improve readiness.',
        },
    ],
}


def _make_assessment_with_text(field_path: str, text: str) -> dict:
    """Create a copy of the base assessment with a specific text value injected.
    Supports paths like 'recommendations[0].expected_impact'.
    """
    import copy
    assessment = copy.deepcopy(BASE_AI_ASSESSMENT)

    # Parse path into segments, handling array index notation
    segments = []
    for part in field_path.split('.'):
        if '[' in part and ']' in part:
            name = part[:part.index('[')]
            idx = int(part[part.index('[') + 1:part.index(']')])
            segments.append(name)
            segments.append(idx)
        else:
            segments.append(part)

    obj = assessment
    for seg in segments[:-1]:
        if isinstance(seg, int):
            obj = obj[seg]
        else:
            obj = obj[seg]
    final = segments[-1]
    if isinstance(final, int):
        obj[final] = text
    else:
        obj[final] = text
    return assessment


# ── Tests ───────────────────────────────────────────────────────────────────

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  PASS: {name}")

    def fail(self, name, msg):
        self.failed += 1
        self.errors.append((name, msg))
        print(f"  FAIL: {name} — {msg}")

    def summary(self):
        total = self.passed + self.failed
        print()
        print("=" * 70)
        print(f"RESULTS: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print()
            print("FAILURES:")
            for name, msg in self.errors:
                print(f"  - {name}: {msg}")
        print("=" * 70)
        return self.failed == 0


def test_pattern_detection(r: TestResult):
    """Verify that each hallucination pattern is detected by regex."""
    print()
    print("[PATTERN DETECTION]")
    test_cases = [
        ("committed time", "already committed 2 hours", "already committed"),
        ("existing commitments", "existing commitments prevent studying", "existing commitments"),
        ("prior commitments", "prior commitments conflict", "prior commitments"),
        ("academic probation", "risk of academic probation", "academic probation policy"),
        ("academic dismissal", "risk of academic dismissal", "academic dismissal policy"),
        ("academic warning", "may receive academic warning", "academic warning policy"),
        ("suspension", "risk of suspension", "suspension policy"),
        ("expulsion", "risk of expulsion", "expulsion policy"),
        ("dean's list", "eligible for dean's list", "dean's list policy"),
        ("GPA cutoff", "GPA cutoff is 2.0", "GPA cutoff policy"),
        ("tutoring", "visit tutoring center", "invented tutoring resource"),
        ("office hours", "attend office hours", "invented office hours"),
        ("study group", "join a study group", "invented study group"),
        ("counseling", "seek counseling", "invented counseling resource"),
        ("mental health", "mental health resources", "invented mental health resource"),
        ("writing center", "visit the writing center", "invented writing center"),
        ("academic advisor", "consult academic advisor", "invented advisor"),
        ("syllabus", "check the syllabus", "invented syllabus context"),
        ("grading rubric", "follow the grading rubric", "invented rubric context"),
        ("extension", "request an extension", "invented extension policy"),
        ("late penalty", "late penalty applies", "late penalty policy"),
        ("incomplete", "file for incomplete", "invented incomplete policy"),
        ("no study time", "no study time remains", "claim of no study time"),
        ("zero time", "zero time available", "claim of zero time"),
        ("will raise grade", "will raise the grade", "guaranteed grade improvement"),
        ("will improve grade", "will improve the grade", "guaranteed grade improvement"),
        ("will reduce burnout", "will reduce burnout", "guaranteed burnout reduction"),
        ("will ensure", "will ensure success", "guaranteed outcome"),
        ("will guarantee", "will guarantee results", "guaranteed outcome"),
        ("guaranteed to", "guaranteed to help", "guaranteed outcome"),
        ("definitely will", "definitely will improve", "definite outcome claim"),
        ("certainly will", "certainly will help", "certain outcome claim"),
        ("will pass", "student will pass", "guaranteed pass claim"),
        ("will fail", "student will fail", "guaranteed fail claim"),
        ("should pass", "student should pass", "predicted pass claim"),
        ("likely to pass", "likely to pass the course", "predicted pass claim"),
        ("expected to pass", "expected to pass", "predicted pass claim"),
        ("will raise grade to 85", "will raise grade to 85%", "specific grade prediction"),
        ("grade will reach 90", "grade will reach 90%", "specific grade prediction"),
        ("adds earned points", "adds earned points and raises the grade", "unsupported grade claim"),
        ("burnout impairs", "burnout impairs health", "unsupported health claim"),
        ("leads to burnout", "leads to burnout", "unsupported health claim"),
        ("all assignments can be completed", "all assignments can be completed", "false completeness claim"),
        ("complete all tasks", "can complete all tasks", "false completeness claim"),
        ("finish all work", "finish all work this week", "false completeness claim"),
    ]

    for name, text, expected_label in test_cases:
        found = False
        for pattern, label in _HALLUCINATION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                found = True
                if label == expected_label:
                    r.ok(f"pattern: {name}")
                else:
                    r.fail(f"pattern: {name}", f"matched wrong label: {label} (expected {expected_label})")
                break
        if not found:
            r.fail(f"pattern: {name}", f"NOT DETECTED for text: '{text}'")


def test_sanitize_catches_violations(r: TestResult):
    """Verify that _sanitize_ai_output catches and rewrites violations."""
    print()
    print("[SANITIZE CATCHES VIOLATIONS]")
    service = AnalysisService()

    violations_to_test = [
        ("overall_summary", "This will definitely raise the grade to 85%"),
        ("overall_summary", "All assignments can be completed this week"),
        ("overall_summary", "Visit tutoring center for help"),
        ("overall_summary", "Request an extension from the professor"),
        ("overall_summary", "Risk of academic probation"),
        ("overall_summary", "Student will pass the course"),
        ("recommendations[0].expected_impact", "Will guarantee improved grades"),
        ("explanations[0].expected_result", "Will definitely improve performance"),
        ("explanations[0].why_this_action", "Certainly will reduce burnout"),
        ("risk_factors[0].explanation", "Burnout impairs health significantly"),
    ]

    for field_path, violation_text in violations_to_test:
        assessment = _make_assessment_with_text(field_path, violation_text)
        sanitized = service._sanitize_ai_output(assessment, BASE_STUDENT_DATA)

        # Get the sanitized value
        sanitized_text = _get_nested_value(sanitized, field_path)

        # Check that the violation was caught (text changed or pattern no longer matches)
        still_violates = False
        for pattern, label in _HALLUCINATION_PATTERNS:
            if re.search(pattern, sanitized_text, re.IGNORECASE):
                still_violates = True
                break

        if still_violates:
            r.fail(f"sanitize: {field_path}", f"still contains violation: '{sanitized_text[:80]}'")
        else:
            r.ok(f"sanitize: {field_path}")


def _get_nested_value(obj, field_path: str):
    """Get a value from a nested dict using a path like 'recommendations[0].expected_impact'."""
    segments = []
    for part in field_path.split('.'):
        if '[' in part and ']' in part:
            name = part[:part.index('[')]
            idx = int(part[part.index('[') + 1:part.index(']')])
            segments.append(name)
            segments.append(idx)
        else:
            segments.append(part)

    for seg in segments:
        if isinstance(seg, int):
            obj = obj[seg]
        else:
            obj = obj[seg]
    return obj


def test_sanitize_preserves_clean_text(r: TestResult):
    """Verify that _sanitize_ai_output does NOT rewrite clean text."""
    print()
    print("[SANITIZE PRESERVES CLEAN TEXT]")
    service = AnalysisService()

    # Use student_data where workload fits (2h tasks, 4h available)
    clean_student_data = {
        'current_grade': 72,
        'stress_level': 7,
        'available_time': 4,
        'tasks': [
            {'name': 'A', 'course': 'A', 'estimated_time': 1, 'due_in_hours': 72, 'missing': False},
        ],
    }

    clean_texts = [
        ("overall_summary", "Grade: 72%. Stress: 7/10. Workload fits within available time."),
        ("overall_summary", "Academic risk is LOW. Burnout risk is HIGH."),
        ("recommendations[0].expected_impact", "May help improve outcomes given current constraints."),
        ("explanations[0].expected_result", "Could improve readiness for upcoming deadlines."),
        ("explanations[0].why_this_action", "May help reduce immediate deadline pressure."),
        ("risk_factors[0].explanation", "Workload of 1h fits within 4h/week available time."),
    ]

    for field_path, clean_text in clean_texts:
        assessment = _make_assessment_with_text(field_path, clean_text)
        sanitized = service._sanitize_ai_output(assessment, clean_student_data)
        sanitized_text = _get_nested_value(sanitized, field_path)

        if sanitized_text != clean_text:
            r.fail(f"preserve: {field_path}", f"clean text was changed: '{sanitized_text[:80]}'")
        else:
            r.ok(f"preserve: {field_path}")


def test_deterministic_authority_overrides(r: TestResult):
    """Verify that _enforce_deterministic_authority overrides AI values."""
    print()
    print("[DETERMINISTIC AUTHORITY OVERRIDES]")
    service = AnalysisService()

    # Create assessment with wrong scores
    assessment = {
        'academic_risk': {'score': 99, 'level': 'CRITICAL', 'explanation': 'Wrong score.'},
        'burnout_risk': {'score': 5, 'level': 'LOW', 'explanation': 'Wrong score.'},
        'recovery_score': {'score': 90, 'explanation': 'Wrong score.'},
        'overall_summary': 'Test.',
        'risk_factors': [],
        'priorities': [],
        'recommendations': [],
        'recovery_plan': [],
        'explanations': [],
    }

    from backend.services.risk_engine import RiskEngine
    engine = RiskEngine()
    risk_signals = engine.compute_all_signals(BASE_STUDENT_DATA)

    overridden = service._enforce_deterministic_authority(assessment, risk_signals, BASE_STUDENT_DATA)

    expected_academic = int(risk_signals['academic_risk'] * 100)
    expected_burnout = int(risk_signals['burnout_risk'] * 100)
    expected_recovery = int(risk_signals['recovery_feasibility'] * 100)

    if overridden['academic_risk']['score'] != expected_academic:
        r.fail("override: academic_risk score", f"{overridden['academic_risk']['score']} != {expected_academic}")
    else:
        r.ok("override: academic_risk score")

    if overridden['burnout_risk']['score'] != expected_burnout:
        r.fail("override: burnout_risk score", f"{overridden['burnout_risk']['score']} != {expected_burnout}")
    else:
        r.ok("override: burnout_risk score")

    if overridden['recovery_score']['score'] != expected_recovery:
        r.fail("override: recovery_score", f"{overridden['recovery_score']['score']} != {expected_recovery}")
    else:
        r.ok("override: recovery_score")

    # Verify priorities are overridden
    expected_priorities = service._build_priorities(BASE_STUDENT_DATA.get('tasks', []), risk_signals)
    if len(overridden['priorities']) != len(expected_priorities):
        r.fail("override: priorities count", f"{len(overridden['priorities'])} != {len(expected_priorities)}")
    else:
        r.ok("override: priorities count")


def test_recovery_plan_budget_enforced(r: TestResult):
    """Verify that recovery plan total cannot exceed available minutes."""
    print()
    print("[RECOVERY PLAN BUDGET]")
    from backend.services.groq_service import _validate_recovery_plan

    # Create assessment with plan exceeding budget
    assessment = {
        'recovery_plan': [
            {
                'date': '2026-08-12',
                'tasks': [
                    {'course': 'Math', 'task': 'Study', 'duration_minutes': 200, 'priority': 'HIGH', 'reason': 'Urgent.'},
                ],
                'total_study_minutes': 200,
            }
        ],
    }

    student_data = {'available_time': 3}  # 180 minutes
    validated = _validate_recovery_plan(assessment, student_data)

    total = sum(d.get('total_study_minutes', 0) for d in validated.get('recovery_plan', []))
    if total > 180:
        r.fail("budget: total exceeds 180", f"total={total}")
    else:
        r.ok(f"budget: total={total} <= 180")


def test_recovery_plan_course_validation(r: TestResult):
    """Verify that recovery plan tasks reference valid courses only."""
    print()
    print("[RECOVERY PLAN COURSE VALIDATION]")
    service = AnalysisService()

    plan = [
        {
            'date': '2026-08-12',
            'tasks': [
                {'course': 'Mathematics', 'task': 'Study', 'duration_minutes': 60, 'priority': 'HIGH', 'reason': 'Urgent.'},
                {'course': 'Invented Course', 'task': 'Study', 'duration_minutes': 30, 'priority': 'LOW', 'reason': 'Test.'},
            ],
            'total_study_minutes': 90,
        }
    ]

    validated = service._validate_recovery_plan_courses(plan, BASE_STUDENT_DATA)

    courses_found = set()
    for day in validated:
        for task in day.get('tasks', []):
            courses_found.add(task.get('course', '').lower())

    if 'invented course' in courses_found:
        r.fail("course validation", "invented course was not removed")
    else:
        r.ok("course validation: invented course removed")


def test_triage_language_enforced(r: TestResult):
    """Verify that overall_summary includes triage language when workload exceeds capacity."""
    print()
    print("[TRIAGE LANGUAGE ENFORCEMENT]")
    service = AnalysisService()

    # Create assessment without triage language
    assessment = {
        'overall_summary': 'Grade is 72%. Everything looks fine.',
    }

    student_data = {
        'current_grade': 72,
        'stress_level': 7,
        'available_time': 3,
        'tasks': [
            {'estimated_time': 5, 'course': 'A'},
            {'estimated_time': 5, 'course': 'B'},
        ],
    }

    sanitized = service._sanitize_ai_output(assessment, student_data)
    summary = sanitized.get('overall_summary', '')

    triage_keywords = ['triage', 'prioritiz', 'exceeds', 'capacity', 'defer', 'not all assignments']
    has_triage = any(kw in summary.lower() for kw in triage_keywords)

    if has_triage:
        r.ok("triage language: present")
    else:
        r.fail("triage language", f"missing in: '{summary[:100]}'")


def test_evidence_references_input(r: TestResult):
    """Verify that _evidence_references_input detects grounded vs ungrounded evidence."""
    print()
    print("[EVIDENCE GROUNDING]")
    service = AnalysisService()

    # Grounded evidence (workload = 2+3 = 5 hours)
    grounded_cases = [
        "Grade is 72% and stress is 7/10",
        "Available time is 3 hours/week",
        "Workload of 5 hours exceeds capacity",
        "Calculus has a deadline in 72 hours",
    ]

    for evidence in grounded_cases:
        if service._evidence_references_input(evidence, BASE_STUDENT_DATA):
            r.ok(f"grounded: '{evidence[:50]}'")
        else:
            r.fail(f"grounded: '{evidence[:50]}'", "detected as ungrounded")

    # Ungrounded evidence
    ungrounded_cases = [
        "Student has a history of poor performance",
        "The school requires a 2.0 GPA",
        "Past semesters show declining grades",
        "External factors suggest stress",
    ]

    for evidence in ungrounded_cases:
        if not service._evidence_references_input(evidence, BASE_STUDENT_DATA):
            r.ok(f"ungrounded: '{evidence[:50]}'")
        else:
            r.fail(f"ungrounded: '{evidence[:50]}'", "detected as grounded")


def main():
    print("=" * 70)
    print("ADVERSARIAL HALLUCINATION TESTS")
    print("=" * 70)

    r = TestResult()

    test_pattern_detection(r)
    test_sanitize_catches_violations(r)
    test_sanitize_preserves_clean_text(r)
    test_deterministic_authority_overrides(r)
    test_recovery_plan_budget_enforced(r)
    test_recovery_plan_course_validation(r)
    test_triage_language_enforced(r)
    test_evidence_references_input(r)

    return r.summary()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
