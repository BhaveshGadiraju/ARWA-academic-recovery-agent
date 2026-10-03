import type { Dashboard } from '@/lib/types';
import { formatMinutes } from '@/lib/format';

/** Four at-a-glance facts about today. */
export function TodayStrip({ today }: { today: Dashboard['today'] }) {
  const stats = [
    { label: 'Academic load', value: today.academic_load },
    { label: 'Deadline pressure', value: today.deadline_pressure },
    { label: 'Study time left today', value: today.available_minutes_today ? formatMinutes(today.available_minutes_today) : 'None' },
    {
      label: 'Due this week',
      value: `${today.tasks_remaining} task${today.tasks_remaining === 1 ? '' : 's'}`,
      note: today.overdue_count ? `${today.overdue_count} overdue` : undefined,
    },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {stats.map((s) => (
        <div key={s.label} className="rounded-2xl border border-line bg-surface px-4 py-3.5">
          <p className="text-xs text-muted">{s.label}</p>
          <p className="mt-1 text-[17px] font-semibold tracking-tight">{s.value}</p>
          {s.note && <p className="text-xs font-medium text-bad">{s.note}</p>}
        </div>
      ))}
    </div>
  );
}
