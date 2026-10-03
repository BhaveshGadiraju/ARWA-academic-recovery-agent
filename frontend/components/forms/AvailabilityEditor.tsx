'use client';

import type { AvailabilityDay } from '@/lib/types';
import { WEEKDAYS, formatMinutes } from '@/lib/format';
import { Input, Select } from '@/components/ui/Field';

const MINUTE_OPTIONS = [0, 30, 60, 90, 120, 150, 180, 240, 300, 360, 480];

const isWeekend = (weekday: number) => weekday >= 5;

const PRESETS: { label: string; minutesFor: (weekday: number) => number }[] = [
  { label: '2h every weekday', minutesFor: (d) => (isWeekend(d) ? 0 : 120) },
  { label: '2h every day', minutesFor: () => 120 },
  { label: '1h weekdays + 3h weekends', minutesFor: (d) => (isWeekend(d) ? 180 : 60) },
];

interface Props {
  value: AvailabilityDay[];
  onChange: (days: AvailabilityDay[]) => void;
}

/** Weekly study-time editor. One row per weekday; 0 minutes means no study that day. */
export function AvailabilityEditor({ value, onChange }: Props) {
  const day = (weekday: number): AvailabilityDay =>
    value.find((d) => d.weekday === weekday) ?? { weekday, minutes: 0, start_time: '18:00' };

  const update = (weekday: number, patch: Partial<AvailabilityDay>) => {
    const next = WEEKDAYS.map((_, i) => (i === weekday ? { ...day(i), ...patch } : day(i)));
    onChange(next);
  };

  const applyPreset = (preset: (typeof PRESETS)[number]) => {
    onChange(WEEKDAYS.map((_, i) => ({ ...day(i), minutes: preset.minutesFor(i) })));
  };

  const total = value.reduce((sum, d) => sum + d.minutes, 0);

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => applyPreset(p)}
            className="rounded-full border border-line-strong px-3 py-1.5 text-[13px] text-ink-soft hover:bg-sunken"
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="divide-y divide-line rounded-2xl border border-line">
        {WEEKDAYS.map((name, i) => {
          const d = day(i);
          return (
            <div key={name} className="flex items-center gap-3 px-4 py-2.5">
              <span className="w-24 text-sm font-medium">{name}</span>
              <Select
                aria-label={`${name} study time`}
                value={d.minutes}
                onChange={(e) => update(i, { minutes: Number(e.target.value) })}
                className="!h-9 flex-1 text-sm"
              >
                {MINUTE_OPTIONS.map((m) => (
                  <option key={m} value={m}>
                    {m === 0 ? 'No study' : formatMinutes(m)}
                  </option>
                ))}
              </Select>
              <Input
                aria-label={`${name} start time`}
                type="time"
                value={d.start_time}
                disabled={d.minutes === 0}
                onChange={(e) => update(i, { start_time: e.target.value || '18:00' })}
                className="!h-9 w-[118px] text-sm disabled:opacity-40"
              />
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-sm text-muted">
        Total: <span className="font-medium text-ink">{formatMinutes(total)}</span> per week
      </p>
    </div>
  );
}
