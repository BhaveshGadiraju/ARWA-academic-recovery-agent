'use client';

import { Field, Input, Select } from '@/components/ui/Field';

export interface ProfileValues {
  full_name: string;
  school: string;
  major: string;
  year_in_school: string;
}

const YEARS = ['First year', 'Second year', 'Third year', 'Fourth year', 'Fifth year+', 'Graduate'];

interface Props {
  values: ProfileValues;
  onChange: (values: ProfileValues) => void;
}

/** Name, school, major, and year. Controlled, so onboarding and settings share it. */
export function ProfileFields({ values, onChange }: Props) {
  const set = (key: keyof ProfileValues) => (e: { target: { value: string } }) => onChange({ ...values, [key]: e.target.value });
  return (
    <div className="space-y-4">
      <Field label="Your name">
        <Input value={values.full_name} onChange={set('full_name')} maxLength={120} autoComplete="name" />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="School (optional)">
          <Input value={values.school} onChange={set('school')} maxLength={120} />
        </Field>
        <Field label="Major (optional)">
          <Input value={values.major} onChange={set('major')} maxLength={120} />
        </Field>
      </div>
      <Field label="Year (optional)">
        <Select value={values.year_in_school} onChange={set('year_in_school')}>
          <option value="">Select…</option>
          {YEARS.map((y) => (
            <option key={y}>{y}</option>
          ))}
        </Select>
      </Field>
    </div>
  );
}

export function profileValues(profile: { full_name: string | null; school: string | null; major: string | null; year_in_school: string | null }): ProfileValues {
  return {
    full_name: profile.full_name ?? '',
    school: profile.school ?? '',
    major: profile.major ?? '',
    year_in_school: profile.year_in_school ?? '',
  };
}

/** Convert form values to a PATCH body (blank optional fields become null). */
export function profilePayload(values: ProfileValues) {
  return {
    full_name: values.full_name.trim(),
    school: values.school.trim() || null,
    major: values.major.trim() || null,
    year_in_school: values.year_in_school || null,
  };
}
