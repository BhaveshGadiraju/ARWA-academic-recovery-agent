"""
ARWA recovery planner.

Schedules the student's real, incomplete assignments into their real study
windows, in priority order, for the next few days. It never invents work:
every study block points at a stored assignment, and anything that cannot fit
before its due date is reported as unscheduled instead of being hidden.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from backend.services.academic_engine import window_minutes_left_today
from backend.services.domain import StudentSnapshot
from models.insights import PlanBlock, PlanDay, PriorityItem, RecoveryPlan, UnscheduledWork

STANDARD_BLOCK_MINUTES = 50
SHORT_BLOCK_MINUTES = 30
BREAK_MINUTES = 10
MIN_BLOCK_MINUTES = 15
HIGH_STRESS_LEVEL = 8
DEFAULT_HORIZON_DAYS = 7


def _ceil_to_five(moment: datetime) -> datetime:
    """Round a time up to the next 5-minute mark."""
    moment = moment.replace(second=0, microsecond=0)
    extra = (-moment.minute) % 5
    return moment + timedelta(minutes=extra)


def _day_label(offset: int, moment: datetime) -> str:
    """'Today', 'Tomorrow', or the weekday name."""
    if offset == 0:
        return "Today"
    if offset == 1:
        return "Tomorrow"
    return moment.strftime("%A")


def _block_length(snapshot: StudentSnapshot) -> int:
    """Shorter focus blocks when the student reports high stress."""
    stress = snapshot.wellness.stress_level if snapshot.wellness else None
    if stress is not None and stress >= HIGH_STRESS_LEVEL:
        return SHORT_BLOCK_MINUTES
    return STANDARD_BLOCK_MINUTES


def build_plan(
    snapshot: StudentSnapshot,
    priorities: List[PriorityItem],
    days: int = DEFAULT_HORIZON_DAYS,
) -> RecoveryPlan:
    """Greedy, deadline-aware schedule over the next `days` days."""
    today = snapshot.today
    by_id: Dict[str, PriorityItem] = {p.assignment_id: p for p in priorities}
    remaining: "OrderedDict[str, int]" = OrderedDict(
        (p.assignment_id, p.remaining_minutes) for p in priorities if p.remaining_minutes > 0
    )
    block_length = _block_length(snapshot)
    plan_days: List[PlanDay] = []

    for offset in range(days):
        day = today + timedelta(days=offset)
        availability = snapshot.availability.get(day.weekday())
        if availability is None or availability.minutes <= 0:
            plan_days.append(PlanDay(
                date=day, label=_day_label(offset, snapshot.now), window_minutes=0, study_minutes=0, blocks=[],
            ))
            continue

        window_start = datetime.combine(day, availability.start_time, tzinfo=snapshot.now.tzinfo)
        if offset == 0:
            window = window_minutes_left_today(snapshot.now, availability)
            clock = max(window_start, _ceil_to_five(snapshot.now))
            window = min(window, availability.minutes - max(0, int((clock - window_start).total_seconds() // 60)))
        else:
            window = availability.minutes
            clock = window_start

        blocks = _fill_day(day, max(window, 0), clock, remaining, by_id, block_length, today)
        plan_days.append(PlanDay(
            date=day,
            label=_day_label(offset, window_start),
            window_minutes=max(window, 0),
            study_minutes=sum(b.minutes for b in blocks if b.kind == "study"),
            blocks=blocks,
        ))

    horizon_end = today + timedelta(days=days - 1)
    unscheduled = [
        UnscheduledWork(
            assignment_id=aid,
            title=by_id[aid].title,
            course_name=by_id[aid].course_name,
            due_date=by_id[aid].due_date,
            unscheduled_minutes=minutes,
        )
        for aid, minutes in remaining.items()
        if minutes > 0 and by_id[aid].due_date <= horizon_end
    ]

    required = sum(p.remaining_minutes for p in priorities if p.due_date <= horizon_end)
    planned = sum(d.study_minutes for d in plan_days)
    return RecoveryPlan(
        generated_at=snapshot.now,
        days=plan_days,
        unscheduled=unscheduled,
        required_minutes=required,
        planned_minutes=planned,
        is_feasible=not unscheduled,
    )


def _next_assignment(
    day,
    remaining: "OrderedDict[str, int]",
    by_id: Dict[str, PriorityItem],
    today,
    minutes_today: Dict[str, int],
    daily_cap: int,
) -> Optional[str]:
    """Highest-priority item with work left that is still due today or later (or already overdue).

    One assignment gets at most `daily_cap` minutes per day while other work is
    waiting, so neither a big exam nor overdue work can take a whole evening
    from something else that is due soon.
    """
    candidates = [
        aid for aid, minutes in remaining.items()
        if minutes > 0 and (by_id[aid].due_date >= day or by_id[aid].due_date < today)
    ]
    for aid in candidates:
        room = daily_cap - minutes_today.get(aid, 0)
        if room >= min(MIN_BLOCK_MINUTES, remaining[aid]):
            return aid
    return candidates[0] if candidates else None


def _fill_day(
    day,
    window: int,
    clock: datetime,
    remaining: "OrderedDict[str, int]",
    by_id: Dict[str, PriorityItem],
    block_length: int,
    today,
) -> List[PlanBlock]:
    """Fill one study window with study blocks separated by short breaks."""
    blocks: List[PlanBlock] = []
    left = window
    minutes_today: Dict[str, int] = {}
    daily_cap = max(block_length, min(2 * block_length, window // 2))

    while left >= MIN_BLOCK_MINUTES:
        aid = _next_assignment(day, remaining, by_id, today, minutes_today, daily_cap)
        if aid is None:
            break
        chunk = min(block_length, remaining[aid], left)
        room = daily_cap - minutes_today.get(aid, 0)
        if room >= min(MIN_BLOCK_MINUTES, remaining[aid]):
            chunk = min(chunk, room)
        if chunk < MIN_BLOCK_MINUTES and remaining[aid] > chunk:
            break

        item = by_id[aid]
        end = clock + timedelta(minutes=chunk)
        blocks.append(PlanBlock(
            kind="study",
            start=clock.strftime("%H:%M"),
            end=end.strftime("%H:%M"),
            minutes=chunk,
            assignment_id=aid,
            title=item.title,
            course_name=item.course_name,
            category=item.category,
            due_date=item.due_date,
        ))
        remaining[aid] -= chunk
        minutes_today[aid] = minutes_today.get(aid, 0) + chunk
        left -= chunk
        clock = end

        next_aid = _next_assignment(day, remaining, by_id, today, minutes_today, daily_cap)
        if next_aid is None or left < BREAK_MINUTES + MIN_BLOCK_MINUTES:
            break
        break_end = clock + timedelta(minutes=BREAK_MINUTES)
        blocks.append(PlanBlock(
            kind="break", start=clock.strftime("%H:%M"), end=break_end.strftime("%H:%M"), minutes=BREAK_MINUTES,
        ))
        left -= BREAK_MINUTES
        clock = break_end

    while blocks and blocks[-1].kind == "break":
        blocks.pop()
    return blocks
