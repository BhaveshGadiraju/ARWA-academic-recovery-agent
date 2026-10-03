'use client';

import { useState } from 'react';
import type { AvailabilityDay } from '@/lib/types';
import { useApi } from '@/hooks/useApi';
import { AvailabilityEditor } from '@/components/forms/AvailabilityEditor';
import { FormError } from '@/components/ui/Field';
import { StepFrame } from './StepFrame';

interface Props {
  initial: AvailabilityDay[];
  onSaved: (days: AvailabilityDay[]) => void;
  onBack: () => void;
}

export function StudyTimeStep({ initial, onSaved, onBack }: Props) {
  const request = useApi();
  const [days, setDays] = useState<AvailabilityDay[]>(initial);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setError(null);
    setBusy(true);
    try {
      const saved = await request<AvailabilityDay[]>('PUT', '/availability', {
        days: days.filter((d) => d.minutes > 0),
      });
      onSaved(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save your study time.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <StepFrame
      step={4}
      total={5}
      title="When can you study?"
      subtitle="Be realistic. ARWA only schedules work inside these windows, and tells you when it doesn’t fit."
      onBack={onBack}
      onNext={save}
      busy={busy}
      nextDisabled={!days.some((d) => d.minutes > 0)}
    >
      <AvailabilityEditor value={days} onChange={setDays} />
      <div className="mt-4">
        <FormError message={error} />
      </div>
    </StepFrame>
  );
}
