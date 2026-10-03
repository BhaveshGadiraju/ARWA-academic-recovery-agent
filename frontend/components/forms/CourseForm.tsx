'use client';

import { useState, type FormEvent } from 'react';
import type { Course } from '@/lib/types';
import { Button } from '@/components/ui/Button';
import { Field, FormError, Input } from '@/components/ui/Field';

export interface CourseValues {
  name: string;
  code: string | null;
  credits: number;
  target_grade: number | null;
}

interface CourseFormProps {
  initial?: Course;
  submitLabel?: string;
  onSubmit: (values: CourseValues) => Promise<void>;
}

export function CourseForm({ initial, submitLabel = 'Add course', onSubmit }: CourseFormProps) {
  const [name, setName] = useState(initial?.name ?? '');
  const [code, setCode] = useState(initial?.code ?? '');
  const [credits, setCredits] = useState(String(initial?.credits ?? 3));
  const [target, setTarget] = useState(initial?.target_grade != null ? String(initial.target_grade) : '');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onSubmit({
        name: name.trim(),
        code: code.trim() || null,
        credits: Number(credits) || 3,
        target_grade: target === '' ? null : Number(target),
      });
      if (!initial) {
        setName('');
        setCode('');
        setTarget('');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save the course.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-[1fr_140px]">
        <Field label="Course name">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Organic Chemistry" required maxLength={120} />
        </Field>
        <Field label="Code (optional)">
          <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="CHEM 241" maxLength={30} />
        </Field>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Credits">
          <Input type="number" min={0.5} max={12} step={0.5} value={credits} onChange={(e) => setCredits(e.target.value)} />
        </Field>
        <Field label="Target grade % (optional)">
          <Input type="number" min={0} max={100} value={target} onChange={(e) => setTarget(e.target.value)} placeholder="85" />
        </Field>
      </div>
      <FormError message={error} />
      <Button type="submit" variant={initial ? 'primary' : 'secondary'} loading={saving} disabled={!name.trim()} className="w-full sm:w-auto">
        {submitLabel}
      </Button>
    </form>
  );
}
