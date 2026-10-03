'use client';

import { useState } from 'react';
import type { Profile, Semester } from '@/lib/types';
import { useApi } from '@/hooks/useApi';
import { useAuth } from '@/contexts/AuthContext';
import { Field, FormError, Input } from '@/components/ui/Field';
import { ProfileFields, profilePayload, profileValues } from '@/components/forms/ProfileFields';
import type { OnboardingData } from './types';
import { StepFrame } from './StepFrame';

function suggestedTerm(now = new Date()): string {
  const month = now.getMonth();
  const season = month >= 7 ? 'Fall' : month >= 4 ? 'Summer' : 'Spring';
  return `${season} ${now.getFullYear()}`;
}

function browserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/New_York';
  } catch {
    return 'America/New_York';
  }
}

interface Props {
  data: OnboardingData;
  onSaved: (patch: { profile: Profile; semester: Semester }) => void;
}

export function ProfileStep({ data, onSaved }: Props) {
  const request = useApi();
  const { user } = useAuth();
  const [values, setValues] = useState(() => {
    const initial = profileValues(data.profile);
    return { ...initial, full_name: initial.full_name || ((user?.user_metadata?.full_name as string) ?? '') };
  });
  const [term, setTerm] = useState(data.semester?.name ?? suggestedTerm());
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setError(null);
    setBusy(true);
    try {
      const profile = await request<Profile>('PATCH', '/profile', { ...profilePayload(values), timezone: browserTimezone() });
      const semester = data.semester
        ? await request<Semester>('PATCH', `/semesters/${data.semester.id}`, { name: term.trim() })
        : await request<Semester>('POST', '/semesters', { name: term.trim(), is_current: true });
      onSaved({ profile, semester });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save your profile.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <StepFrame
      step={1}
      total={5}
      title="Let’s set up your semester"
      subtitle="A few basics so ARWA can plan around your real schedule."
      onNext={save}
      busy={busy}
      nextDisabled={!values.full_name.trim() || !term.trim()}
    >
      <div className="space-y-4">
        <ProfileFields values={values} onChange={setValues} />
        <Field label="Current term">
          <Input value={term} onChange={(e) => setTerm(e.target.value)} maxLength={80} />
        </Field>
        <FormError message={error} />
      </div>
    </StepFrame>
  );
}
