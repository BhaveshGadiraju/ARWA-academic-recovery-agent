import type { PlanDay } from '@/lib/types';
import { CATEGORY_LABEL, formatClock, formatDue, formatMinutes } from '@/lib/format';
import type { FocusTarget } from '@/components/tasks/FocusSession';

interface Props {
  day: PlanDay;
  onStart?: (target: FocusTarget) => void;
}

function emptyMessage(day: PlanDay): string {
  if (day.window_minutes) return 'Nothing scheduled. You’re ahead for this day.';
  // Today's window only counts time that is still ahead, so 0 can mean "already over".
  return day.label === 'Today' ? 'No study time left today.' : 'No study time set for this day.';
}

/** One day of the plan as a vertical timeline of study blocks and breaks. */
export function PlanTimeline({ day, onStart }: Props) {
  if (!day.blocks.length) {
    return (
      <p className="rounded-2xl border border-dashed border-line-strong px-4 py-5 text-center text-sm text-muted">
        {emptyMessage(day)}
      </p>
    );
  }
  return (
    <ol className="relative space-y-2 pl-6">
      <span aria-hidden className="absolute bottom-3 left-[7px] top-3 w-px bg-line" />
      {day.blocks.map((block, i) =>
        block.kind === 'break' ? (
          <li key={i} className="relative py-1 text-xs text-faint">
            <span aria-hidden className="absolute -left-[21px] top-2 h-1.5 w-1.5 rounded-full bg-line-strong" />
            {formatClock(block.start)} · {block.minutes}m break
          </li>
        ) : (
          <li key={i} className="relative">
            <span aria-hidden className="absolute -left-6 top-4 h-3.5 w-3.5 rounded-full border-2 border-ink bg-surface" />
            <div className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-surface px-4 py-3">
              <div className="min-w-0">
                <p className="text-xs font-medium tabular-nums text-muted">
                  {formatClock(block.start)} – {formatClock(block.end)} · {formatMinutes(block.minutes)}
                </p>
                <p className="mt-0.5 truncate text-[15px] font-medium">{block.title}</p>
                <p className="truncate text-xs text-faint">
                  {[block.course_name, block.category && CATEGORY_LABEL[block.category], block.due_date && formatDue(block.due_date)]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              </div>
              {onStart && block.assignment_id && (
                <button
                  onClick={() =>
                    onStart({ assignmentId: block.assignment_id!, title: block.title ?? '', plannedMinutes: block.minutes })
                  }
                  className="shrink-0 rounded-full border border-line-strong px-3 py-1.5 text-[13px] font-medium hover:bg-sunken"
                >
                  Start
                </button>
              )}
            </div>
          </li>
        ),
      )}
    </ol>
  );
}
