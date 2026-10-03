'use client';

import { useState } from 'react';
import { Field, Input } from '@/components/ui/Field';

export interface WellnessValues {
  stress_level: number;
  sleep_hours: number | null;
  energy_level: number | null;
}

/** Optional check-in. Calls onChange as the student adjusts values. */
export function WellnessFields({ onChange }: { onChange: (values: WellnessValues) => void }) {
  const [stress, setStress] = useState(5);
  const [sleep, setSleep] = useState('');
  const [energy, setEnergy] = useState<number | null>(null);

  const emit = (next: Partial<{ stress: number; sleep: string; energy: number | null }>) => {
    const values = { stress, sleep, energy, ...next };
    onChange({
      stress_level: values.stress,
      sleep_hours: values.sleep === '' ? null : Number(values.sleep),
      energy_level: values.energy,
    });
  };

  return (
    <div className="space-y-6">
      <Field label={`Stress right now: ${stress}/10`}>
        <input
          type="range"
          min={1}
          max={10}
          value={stress}
          onChange={(e) => {
            setStress(Number(e.target.value));
            emit({ stress: Number(e.target.value) });
          }}
          className="w-full accent-[var(--color-ink)]"
        />
        <div className="mt-1 flex justify-between text-xs text-faint">
          <span>Calm</span>
          <span>Overwhelmed</span>
        </div>
      </Field>
      <Field label="Sleep last night (hours)">
        <Input
          type="number"
          min={0}
          max={24}
          step={0.5}
          value={sleep}
          placeholder="7"
          onChange={(e) => {
            setSleep(e.target.value);
            emit({ sleep: e.target.value });
          }}
        />
      </Field>
      <div>
        <p className="mb-1.5 text-[13px] font-medium text-ink-soft">Energy</p>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => {
                setEnergy(level);
                emit({ energy: level });
              }}
              className={`h-10 flex-1 rounded-xl border text-sm font-medium ${
                energy === level ? 'border-ink bg-ink text-surface' : 'border-line-strong text-ink-soft hover:bg-sunken'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
        <div className="mt-1 flex justify-between text-xs text-faint">
          <span>Drained</span>
          <span>Energised</span>
        </div>
      </div>
    </div>
  );
}
