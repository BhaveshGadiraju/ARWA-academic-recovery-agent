import type { Progress } from '@/lib/types';
import { formatShortDate } from '@/lib/format';

/** Assignments completed per week, split into on time and late. */
export function WeeklyCompletion({ weeks }: { weeks: Progress['weekly_completion'] }) {
  const max = Math.max(1, ...weeks.map((w) => w.completed));
  return (
    <ul className="space-y-2.5">
      {weeks.map((w) => (
        <li key={w.week_start} className="flex items-center gap-3 text-sm">
          <span className="w-16 shrink-0 text-xs text-muted">{formatShortDate(w.week_start)}</span>
          <div className="flex h-2.5 flex-1 overflow-hidden rounded-full bg-sunken">
            <div className="h-full bg-good" style={{ width: `${(w.on_time / max) * 100}%` }} />
            <div className="h-full bg-warn" style={{ width: `${((w.completed - w.on_time) / max) * 100}%` }} />
          </div>
          <span className="w-6 shrink-0 text-right text-xs font-medium tabular-nums">{w.completed}</span>
        </li>
      ))}
    </ul>
  );
}
