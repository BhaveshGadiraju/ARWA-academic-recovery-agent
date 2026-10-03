import type { Progress } from '@/lib/types';
import { formatMinutes, parseDate } from '@/lib/format';

/** Studied minutes per day, with the planned amount shown as a faint track. */
export function StudyBars({ days }: { days: Progress['study_days'] }) {
  const max = Math.max(60, ...days.map((d) => Math.max(d.studied_minutes, d.planned_minutes ?? 0)));
  return (
    <div>
      <div className="flex h-36 items-end gap-1.5" role="img" aria-label="Study minutes per day over the last 14 days">
        {days.map((d) => {
          const planned = ((d.planned_minutes ?? 0) / max) * 100;
          const studied = (d.studied_minutes / max) * 100;
          return (
            <div
              key={d.date}
              className="relative flex h-full flex-1 items-end"
              title={`${parseDate(d.date).toLocaleDateString()}: studied ${formatMinutes(d.studied_minutes)}${
                d.planned_minutes != null ? ` of ${formatMinutes(d.planned_minutes)} planned` : ''
              }`}
            >
              <div className="absolute inset-x-0 bottom-0 rounded-md bg-sunken" style={{ height: `${planned}%` }} />
              <div className="relative w-full rounded-md bg-ink transition-[height] duration-700" style={{ height: `${studied}%` }} />
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex gap-1.5 text-[10px] text-faint">
        {days.map((d) => (
          <span key={d.date} className="flex-1 text-center">
            {parseDate(d.date).toLocaleDateString(undefined, { weekday: 'narrow' })}
          </span>
        ))}
      </div>
      <div className="mt-3 flex gap-4 text-xs text-muted">
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-ink" /> Studied</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-sunken" /> Planned</span>
      </div>
    </div>
  );
}
