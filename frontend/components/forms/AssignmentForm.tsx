'use client';

import { useState, type FormEvent } from 'react';
import type { Assignment, AssignmentInput, Category, Course } from '@/lib/types';
import { CATEGORY_LABEL, addDays, toISODate } from '@/lib/format';
import { Button } from '@/components/ui/Button';
import { Field, FormError, Input, Select, Textarea } from '@/components/ui/Field';

interface AssignmentFormProps {
  courses: Course[];
  initial?: Assignment;
  defaultCourseId?: string;
  submitLabel?: string;
  onSubmit: (values: AssignmentInput) => Promise<void>;
}

const CATEGORIES = Object.keys(CATEGORY_LABEL) as Category[];

function optionalNumber(value: string): number | null {
  return value.trim() === '' ? null : Number(value);
}

export function AssignmentForm({ courses, initial, defaultCourseId, submitLabel, onSubmit }: AssignmentFormProps) {
  const [title, setTitle] = useState(initial?.title ?? '');
  const [courseId, setCourseId] = useState(initial?.course_id ?? defaultCourseId ?? courses[0]?.id ?? '');
  const [category, setCategory] = useState<Category>(initial?.category ?? 'homework');
  const [dueDate, setDueDate] = useState(initial?.due_date ?? toISODate(addDays(new Date(), 7)));
  const [hours, setHours] = useState(String(initial?.estimated_hours ?? 2));
  const [possible, setPossible] = useState(initial?.points_possible != null ? String(initial.points_possible) : '');
  const [earned, setEarned] = useState(initial?.points_earned != null ? String(initial.points_earned) : '');
  const [notes, setNotes] = useState(initial?.notes ?? '');
  const [showGrade, setShowGrade] = useState(initial?.points_possible != null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const reset = () => {
    setTitle('');
    setPossible('');
    setEarned('');
    setNotes('');
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    const pointsPossible = optionalNumber(possible);
    const pointsEarned = optionalNumber(earned);
    if (pointsEarned !== null && pointsPossible === null) {
      setError('Add the points possible so ARWA can calculate the grade.');
      return;
    }
    setSaving(true);
    try {
      await onSubmit({
        title: title.trim(),
        course_id: courseId,
        category,
        due_date: dueDate,
        estimated_hours: Number(hours) || 0,
        points_possible: pointsPossible,
        points_earned: pointsEarned,
        notes: notes.trim() || null,
        ...(pointsEarned !== null && !initial ? { completed: true } : {}),
      });
      if (!initial) reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save the assignment.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <Field label="Title">
        <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Problem Set 6" required maxLength={200} />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Course">
          <Select value={courseId} onChange={(e) => setCourseId(e.target.value)} required>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.code || c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Type">
          <Select value={category} onChange={(e) => setCategory(e.target.value as Category)}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {CATEGORY_LABEL[c]}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Due date">
          <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} required />
        </Field>
        <Field label="Estimated hours" hint="Total work, not per day">
          <Input type="number" min={0} max={200} step={0.25} value={hours} onChange={(e) => setHours(e.target.value)} required />
        </Field>
      </div>

      {showGrade ? (
        <div className="grid grid-cols-2 gap-3">
          <Field label="Points earned">
            <Input type="number" min={0} step="any" value={earned} onChange={(e) => setEarned(e.target.value)} placeholder="Not graded yet" />
          </Field>
          <Field label="Points possible">
            <Input type="number" min={0} step="any" value={possible} onChange={(e) => setPossible(e.target.value)} placeholder="100" />
          </Field>
        </div>
      ) : (
        <button type="button" onClick={() => setShowGrade(true)} className="text-sm font-medium text-muted underline underline-offset-4 hover:text-ink">
          + Add points / grade
        </button>
      )}

      {initial && (
        <Field label="Notes (optional)">
          <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={2000} />
        </Field>
      )}

      <FormError message={error} />
      <Button type="submit" loading={saving} disabled={!title.trim() || !courseId} className="w-full sm:w-auto">
        {submitLabel ?? (initial ? 'Save changes' : 'Add assignment')}
      </Button>
    </form>
  );
}
