'use client';

import { useEffect, useState } from 'react';
import type { AvailabilityDay } from '@/lib/types';
import { useApi, useApiData } from '@/hooks/useApi';
import { useProfile } from '@/contexts/ProfileContext';
import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FormError } from '@/components/ui/Field';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingState } from '@/components/ui/States';
import { AvailabilityEditor } from '@/components/forms/AvailabilityEditor';
import { ProfileFields, profilePayload, profileValues } from '@/components/forms/ProfileFields';
import { WellnessFields, type WellnessValues } from '@/components/forms/WellnessForm';

/** Save button state shared by each settings section. */
function useSaver() {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async (action: () => Promise<unknown>) => {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await action();
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save.');
    } finally {
      setSaving(false);
    }
  };
  return { saving, saved, error, save };
}

function SaveRow({ saver, label, disabled }: { saver: ReturnType<typeof useSaver>; label: string; disabled?: boolean }) {
  return (
    <div className="mt-5 space-y-3">
      <FormError message={saver.error} />
      <div className="flex items-center gap-3">
        <Button type="submit" loading={saver.saving} disabled={disabled}>{label}</Button>
        {saver.saved && <span className="animate-fade-up text-sm text-good">Saved</span>}
      </div>
    </div>
  );
}

function ProfileSection() {
  const request = useApi();
  const { profile, refreshProfile } = useProfile();
  const [values, setValues] = useState(() => profileValues(profile));
  const saver = useSaver();

  return (
    <Card>
      <CardHeader title="Profile" />
      <form
        onSubmit={(e) => {
          e.preventDefault();
          saver.save(async () => {
            await request('PATCH', '/profile', profilePayload(values));
            await refreshProfile();
          });
        }}
      >
        <ProfileFields values={values} onChange={setValues} />
        <p className="mt-4 text-xs text-muted">Timezone: {profile.timezone} · Email: {profile.email}</p>
        <SaveRow saver={saver} label="Save profile" disabled={!values.full_name.trim()} />
      </form>
    </Card>
  );
}

function StudyTimeSection() {
  const request = useApi();
  const { data, loading } = useApiData<AvailabilityDay[]>('/availability');
  const [days, setDays] = useState<AvailabilityDay[]>([]);
  const saver = useSaver();

  useEffect(() => {
    if (data) setDays(data);
  }, [data]);

  return (
    <Card>
      <CardHeader title="Weekly study time" />
      {loading ? (
        <LoadingState label="Loading" />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            saver.save(() => request('PUT', '/availability', { days: days.filter((d) => d.minutes > 0) }));
          }}
        >
          <AvailabilityEditor value={days} onChange={setDays} />
          <SaveRow saver={saver} label="Save study time" />
        </form>
      )}
    </Card>
  );
}

function WellnessSection() {
  const request = useApi();
  const [values, setValues] = useState<WellnessValues>({ stress_level: 5, sleep_hours: null, energy_level: null });
  const saver = useSaver();
  return (
    <Card>
      <CardHeader title="Wellness check-in" eyebrow="Optional" />
      <p className="-mt-2 mb-5 text-sm text-muted">High stress makes ARWA plan shorter study blocks. This is never shared.</p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          saver.save(() => request('POST', '/wellness', values));
        }}
      >
        <WellnessFields onChange={setValues} />
        <SaveRow saver={saver} label="Save check-in" />
      </form>
    </Card>
  );
}

export default function SettingsPage() {
  return (
    <div className="animate-fade-up">
      <PageHeader title="Settings" subtitle="Your profile, study time, and check-ins." />
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="space-y-5">
          <ProfileSection />
          <WellnessSection />
        </div>
        <StudyTimeSection />
      </div>
    </div>
  );
}
