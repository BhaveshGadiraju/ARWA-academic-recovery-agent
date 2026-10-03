'use client';

import { useState } from 'react';
import { useApi } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { FormError } from '@/components/ui/Field';
import { WellnessFields, type WellnessValues } from '@/components/forms/WellnessForm';
import { StepFrame } from './StepFrame';

interface Props {
  onBack: () => void;
  onFinish: () => Promise<void>;
}

export function WellnessStep({ onBack, onFinish }: Props) {
  const request = useApi();
  const [values, setValues] = useState<WellnessValues>({ stress_level: 5, sleep_hours: null, energy_level: null });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const finish = async (saveCheckIn: boolean) => {
    setError(null);
    setBusy(true);
    try {
      if (saveCheckIn) await request('POST', '/wellness', values);
      await onFinish();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not finish setup.');
      setBusy(false);
    }
  };

  return (
    <StepFrame
      step={5}
      total={5}
      title="How are you doing?"
      subtitle="Optional. A quick check-in helps ARWA pace your plan. You can skip this."
      onBack={onBack}
      onNext={() => finish(true)}
      nextLabel="Build my plan"
      busy={busy}
      secondary={
        <Button variant="ghost" onClick={() => finish(false)} disabled={busy}>
          Skip
        </Button>
      }
    >
      <WellnessFields onChange={setValues} />
      <div className="mt-4">
        <FormError message={error} />
      </div>
    </StepFrame>
  );
}
