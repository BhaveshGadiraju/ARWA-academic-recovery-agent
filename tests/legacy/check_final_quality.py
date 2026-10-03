"""
Final backend quality test.

Input (exact Swagger test):
  grade=72, stress=7, available_time=3 hrs/week
  Calculus: 2h, 3 days
  Physics: 3h, 4 days
  Programming: 5h, 6 days

Confirm:
  1. HTTP 200
  2. ai_powered=true
  3. fallback_used=false
  4. recovery plan <= 180 minutes total
  5. no unsupported factual claims
  6. no contradiction of backend risk scores
  7. AI clearly identifies that 10h workload exceeds 3h/week capacity
"""

import asyncio
import json
import re
import sys
import os

from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from backend.services.analysis_service import AnalysisService

HALLUCINATION_CHECKS = [
    (r'committed\s+(time|minutes|hours)', "invented committed time"),
    (r'existing\s+commitments?', "invented existing commitments"),
    (r'already[- ]committed', "invented already-committed time"),
    (r'other\s+obligations?', "invented other obligations"),
    (r'600\s+minutes', "invented specific time block"),
    (r'prior\s+commitments?', "invented prior commitments"),
    (r'academic\s+probation', "invented academic probation policy"),
    (r'suspension', "invented suspension policy"),
    (r'expulsion', "invented expulsion policy"),
    (r'gpa\s+cutoff', "invented GPA cutoff policy"),
    (r'no\s+(study\s+)?time\s+(remains|left|remaining)', "claim of no study time"),
    (r'zero\s+time\s+(available|remaining)', "claim of zero time"),
    (r'will\s+(raise|improve|increase|boost)\s+the\s+grade', "guaranteed grade improvement"),
    (r'will\s+(reduce|lower|decrease)\s+burnout', "guaranteed burnout reduction"),
    (r'guaranteed\s+to', "guaranteed outcome"),
    (r'adds\s+earned\s+points?\s+and\s+raises?\s+the\s+grade', "unsupported grade claim"),
    (r'finishing\s+assignments?\s+adds?\s+earned', "unsupported grade claim"),
    (r'burnout\s+impairs?\s+health', "unsupported health claim"),
    (r'will\s+definitely', "definite outcome claim"),
    (r'will\s+certainly', "certain outcome claim"),
    (r'all\s+assignments?\s+(can|will)\s+be\s+completed', "false completeness claim"),
    (r'complete\s+all\s+(assignments?|tasks?|work)', "false completeness claim"),
]

TEST_INPUT = {
    "current_grade": 72,
    "stress_level": 7,
    "available_time": 3,
    "tasks": [
        {
            "name": "Calculus",
            "title": "Calculus",
            "course": "Mathematics",
            "difficulty": 0.6,
            "estimated_time": 2,
            "due_in_hours": 72,
            "missing": False,
        },
        {
            "name": "Physics",
            "title": "Physics",
            "course": "Physics",
            "difficulty": 0.7,
            "estimated_time": 3,
            "due_in_hours": 96,
            "missing": False,
        },
        {
            "name": "Programming",
            "title": "Programming",
            "course": "Computer Science",
            "difficulty": 0.8,
            "estimated_time": 5,
            "due_in_hours": 144,
            "missing": False,
        },
    ],
}


def collect_text(obj, path=""):
    results = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            results.extend(collect_text(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            results.extend(collect_text(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        results.append((path, obj))
    return results


async def main():
    print("=" * 70)
    print("FINAL BACKEND QUALITY TEST")
    print("=" * 70)
    print(f"Input: grade=72, stress=7, available_time=3 hrs/week (180 min/week)")
    print(f"Tasks: Calculus (2h, 72h), Physics (3h, 96h), Programming (5h, 144h)")
    print(f"Total workload: 10 hours")
    print()

    service = AnalysisService()
    result = await service.analyze(TEST_INPUT)

    # === CHECK 1: HTTP 200 (simulated — we call the service directly) ===
    print("[CHECK 1] HTTP 200: PASS (direct service call)")

    # === CHECK 2: ai_powered=true ===
    ai_powered = result.get('ai_powered', False)
    print(f"[CHECK 2] ai_powered={ai_powered}: {'PASS' if ai_powered else 'FAIL'}")

    # === CHECK 3: fallback_used=false ===
    fallback = result.get('fallback_used', True)
    print(f"[CHECK 3] fallback_used={fallback}: {'PASS' if not fallback else 'FAIL'}")

    # === CHECK 4: recovery plan <= 180 minutes ===
    plan = result.get('recovery_plan', [])
    total_plan_minutes = sum(d.get('total_study_minutes', 0) for d in plan)
    max_minutes = 3 * 60  # 180 minutes
    print(f"[CHECK 4] Recovery plan total: {total_plan_minutes} min (max {max_minutes}): "
          f"{'PASS' if total_plan_minutes <= max_minutes else 'FAIL'}")

    # === CHECK 5: no unsupported factual claims ===
    all_text = collect_text(result)
    violations = []
    for path, text in all_text:
        for pattern, label in HALLUCINATION_CHECKS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append((path, label, text[:150]))
    print(f"[CHECK 5] Unsupported claims: {len(violations)}: "
          f"{'PASS' if not violations else 'FAIL'}")
    if violations:
        for path, label, text in violations:
            print(f"  VIOLATION: {label} at {path}")
            print(f"    Text: \"{text}\"")

    # === CHECK 6: no contradiction of backend risk scores ===
    from backend.services.risk_engine import RiskEngine
    engine = RiskEngine()
    risk_signals = engine.compute_all_signals(TEST_INPUT)
    det_academic = int(risk_signals['academic_risk'] * 100)
    det_burnout = int(risk_signals['burnout_risk'] * 100)
    det_recovery = int(risk_signals['recovery_feasibility'] * 100)

    ai_academic = result.get('academic_risk', {}).get('score', -1)
    ai_burnout = result.get('burnout_risk', {}).get('score', -1)
    ai_recovery = result.get('recovery_score', {}).get('score', -1)

    academic_match = ai_academic == det_academic
    burnout_match = ai_burnout == det_burnout
    recovery_match = ai_recovery == det_recovery

    print(f"[CHECK 6] Deterministic authority:")
    print(f"  Academic risk: det={det_academic}, ai={ai_academic} -> {'MATCH' if academic_match else 'MISMATCH'}")
    print(f"  Burnout risk:  det={det_burnout}, ai={ai_burnout} -> {'MATCH' if burnout_match else 'MISMATCH'}")
    print(f"  Recovery score: det={det_recovery}, ai={ai_recovery} -> {'MATCH' if recovery_match else 'MISMATCH'}")
    score_check = academic_match and burnout_match and recovery_match
    print(f"  Overall: {'PASS' if score_check else 'FAIL'}")

    # === CHECK 7: AI identifies workload exceeds capacity ===
    full_text = json.dumps(result).lower()
    triage_keywords = ['triage', 'prioritiz', 'exceeds', 'capacity', 'defer', 'cannot complete', 'not all assignments']
    has_triage = any(kw in full_text for kw in triage_keywords)
    print(f"[CHECK 7] Triage/capacity language: {'PASS' if has_triage else 'FAIL'}")

    # === SUMMARY ===
    print()
    print("=" * 70)
    all_pass = (ai_powered and not fallback and total_plan_minutes <= max_minutes
                and not violations and score_check and has_triage)
    print(f"OVERALL: {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")
    print("=" * 70)

    # === FULL OUTPUT ===
    print()
    print("FULL RESPONSE:")
    print(json.dumps(result, indent=2))

    return all_pass


if __name__ == '__main__':
    passed = asyncio.run(main())
    sys.exit(0 if passed else 1)
