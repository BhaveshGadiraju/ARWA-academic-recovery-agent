"""
Deterministic Risk Engine for ARWA.

Computes objective risk signals from student data.
All calculations are explainable and derived from actual inputs.
No fabricated data.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RiskSignal:
    name: str
    score: float  # 0.0 to 1.0
    severity: str  # LOW, MODERATE, HIGH, CRITICAL
    evidence: str
    explanation: str
    weight: float = 1.0


@dataclass
class TimeBudget:
    total_available_minutes: int
    class_minutes: int = 0
    work_minutes: int = 0
    extracurricular_minutes: int = 0
    study_minutes: int = 0
    committed_minutes: int = 0
    remaining_minutes: int = 0


class RiskEngine:
    """
    Deterministic risk engine that computes objective signals
    from student data. All outputs are explainable.
    """

    def compute_all_signals(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        tasks = student_data.get('tasks', [])
        current_grade = student_data.get('current_grade', 75)
        stress_level = student_data.get('stress_level', 5)
        available_time = student_data.get('available_time', 4)

        academic_signals = self._compute_academic_signals(tasks, current_grade)
        workload_signals = self._compute_workload_signals(tasks, available_time)
        time_signals = self._compute_time_signals(available_time, tasks)
        wellness_signals = self._compute_wellness_signals(stress_level, available_time, tasks)

        academic_risk = self._aggregate_risk([
            academic_signals.get('grade_risk'),
            academic_signals.get('missing_risk'),
            workload_signals.get('workload_risk'),
            workload_signals.get('deadline_risk'),
        ])

        burnout_risk = self._aggregate_risk([
            wellness_signals.get('stress_risk'),
            wellness_signals.get('time_pressure_risk'),
            workload_signals.get('overload_risk'),
        ])

        time_budget = self._compute_time_budget(available_time, tasks)

        recovery_feasibility = self._compute_recovery_feasibility(
            academic_risk, burnout_risk, time_budget
        )

        risk_factors = self._compile_risk_factors(
            academic_signals, workload_signals, time_signals, wellness_signals
        )

        return {
            'academic_risk': academic_risk,
            'burnout_risk': burnout_risk,
            'recovery_feasibility': recovery_feasibility,
            'time_budget': time_budget,
            'risk_factors': risk_factors,
            'academic_signals': academic_signals,
            'workload_signals': workload_signals,
            'time_signals': time_signals,
            'wellness_signals': wellness_signals,
        }

    def _compute_academic_signals(self, tasks: List[Dict], current_grade: float) -> Dict[str, RiskSignal]:
        grade_normalized = max(0, min(1, (100 - current_grade) / 100))
        grade_severity = self._score_to_severity(grade_normalized)

        missing = sum(1 for t in tasks if t.get('missing', False))
        missing_normalized = min(missing / max(len(tasks), 1), 1.0)
        missing_severity = self._score_to_severity(missing_normalized)

        return {
            'grade_risk': RiskSignal(
                name='Current Grade',
                score=grade_normalized,
                severity=grade_severity,
                evidence=f'Current grade: {current_grade}%',
                explanation=f'A grade of {current_grade}% {"indicates academic struggle" if current_grade < 70 else "is below target" if current_grade < 85 else "is acceptable"}',
            ),
            'missing_risk': RiskSignal(
                name='Missing Assignments',
                score=missing_normalized,
                severity=missing_severity,
                evidence=f'{missing} of {len(tasks)} assignments incomplete',
                explanation=f'{missing} incomplete assignment(s) directly impact grade and increase academic risk',
            ),
        }

    def _compute_workload_signals(self, tasks: List[Dict], available_time: float) -> Dict[str, RiskSignal]:
        total_workload = sum(t.get('estimated_time', 0) for t in tasks)
        workload_normalized = min(total_workload / max(available_time * 5, 1), 1.0)
        workload_severity = self._score_to_severity(workload_normalized)

        due_times = [t.get('due_in_hours', 168) for t in tasks if t.get('due_in_hours')]
        urgent = sum(1 for d in due_times if d <= 48)
        urgent_normalized = min(urgent / max(len(tasks), 1), 1.0)
        urgent_severity = self._score_to_severity(urgent_normalized)

        overload_ratio = total_workload / max(available_time, 0.1)
        overload_normalized = min(max(0, (overload_ratio - 1) / 2), 1.0) if overload_ratio > 1 else 0.0
        overload_severity = self._score_to_severity(overload_normalized)

        return {
            'workload_risk': RiskSignal(
                name='Total Workload',
                score=workload_normalized,
                severity=workload_severity,
                evidence=f'{total_workload:.1f} hours estimated workload',
                explanation=f'Total estimated workload of {total_workload:.1f} hours {"exceeds" if total_workload > available_time else "fits within"} {available_time} hours available',
            ),
            'deadline_risk': RiskSignal(
                name='Deadline Pressure',
                score=urgent_normalized,
                severity=urgent_severity,
                evidence=f'{urgent} task(s) due within 48 hours',
                explanation=f'{urgent} task(s) with urgent deadlines create time pressure',
            ),
            'overload_risk': RiskSignal(
                name='Workload Overload',
                score=overload_normalized,
                severity=overload_severity,
                evidence=f'Workload-to-time ratio: {overload_ratio:.1f}x',
                explanation=f'Workload is {overload_ratio:.1f}x the available time' if overload_ratio > 1 else 'Workload fits within available time',
            ),
        }

    def _compute_time_signals(self, available_time: float, tasks: List[Dict]) -> Dict[str, RiskSignal]:
        time_pressure = max(0, min(1, 1 - (available_time / 8)))
        time_severity = self._score_to_severity(time_pressure)

        return {
            'time_pressure_risk': RiskSignal(
                name='Available Time',
                score=time_pressure,
                severity=time_severity,
                evidence=f'{available_time} hours/week available for study',
                explanation=f'{available_time} hours per week {"is limited" if available_time < 3 else "is moderate" if available_time < 5 else "is adequate"} for the current workload',
            ),
        }

    def _compute_wellness_signals(self, stress_level: float, available_time: float, tasks: List[Dict]) -> Dict[str, RiskSignal]:
        stress_normalized = min(stress_level / 10, 1.0)
        stress_severity = self._score_to_severity(stress_normalized)

        time_pressure = max(0, min(1, 1 - (available_time / 8)))
        time_severity = self._score_to_severity(time_pressure)

        total_workload = sum(t.get('estimated_time', 0) for t in tasks)
        overload_ratio = total_workload / max(available_time, 0.1)
        overload_normalized = min(max(0, (overload_ratio - 1) / 2), 1.0) if overload_ratio > 1 else 0.0
        overload_severity = self._score_to_severity(overload_normalized)

        return {
            'stress_risk': RiskSignal(
                name='Stress Level',
                score=stress_normalized,
                severity=stress_severity,
                evidence=f'Self-reported stress: {stress_level}/10',
                explanation=f'Stress level of {stress_level}/10 {"indicates high stress" if stress_level > 7 else "suggests moderate stress" if stress_level > 4 else "is manageable"}',
            ),
            'time_pressure_risk': RiskSignal(
                name='Time Pressure',
                score=time_pressure,
                severity=time_severity,
                evidence=f'{available_time} hours available, {total_workload:.1f} hours needed',
                explanation=f'Time pressure is {"high" if time_pressure > 0.6 else "moderate" if time_pressure > 0.3 else "low"}',
            ),
            'overload_risk': RiskSignal(
                name='Burnout Overload',
                score=overload_normalized,
                severity=overload_severity,
                evidence=f'Workload overload ratio: {overload_ratio:.1f}x',
                explanation=f'Overload {"contributes to burnout" if overload_ratio > 1 else "is within manageable range"}',
            ),
        }

    def _compute_time_budget(self, available_time: float, tasks: List[Dict]) -> TimeBudget:
        total_available = int(available_time * 60)
        total_needed = sum(int(t.get('estimated_time', 0) * 60) for t in tasks)
        remaining = max(0, total_available - total_needed)

        return TimeBudget(
            total_available_minutes=total_available,
            study_minutes=total_available,
            committed_minutes=total_needed,
            remaining_minutes=remaining,
        )

    def _compute_recovery_feasibility(self, academic_risk: float, burnout_risk: float, time_budget: TimeBudget) -> float:
        risk_factor = 1 - (academic_risk + burnout_risk) / 2
        time_factor = min(1.0, time_budget.remaining_minutes / max(time_budget.total_available_minutes, 1)) if time_budget.total_available_minutes > 0 else 0
        return max(0.0, min(1.0, risk_factor * 0.6 + time_factor * 0.4))

    def _aggregate_risk(self, signals: List[Optional[RiskSignal]]) -> float:
        valid = [s for s in signals if s is not None]
        if not valid:
            return 0.5
        weighted_sum = sum(s.score * s.weight for s in valid)
        total_weight = sum(s.weight for s in valid)
        return weighted_sum / total_weight if total_weight > 0 else 0.5

    def _score_to_severity(self, score: float) -> str:
        if score >= 0.8:
            return 'CRITICAL'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MODERATE'
        return 'LOW'

    def _compile_risk_factors(self, academic, workload, time_s, wellness) -> List[Dict]:
        all_signals = []
        for signal_dict in [academic, workload, time_s, wellness]:
            for signal in signal_dict.values():
                if isinstance(signal, RiskSignal):
                    all_signals.append(signal)

        all_signals.sort(key=lambda s: s.score, reverse=True)

        return [
            {
                'factor': s.name,
                'severity': s.severity,
                'impact': int(s.score * 100),
                'evidence': s.evidence,
                'explanation': s.explanation,
            }
            for s in all_signals[:6]
        ]
