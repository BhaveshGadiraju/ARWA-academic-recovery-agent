'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { Assignment, AssignmentInput, CourseDetail } from '@/lib/types';
import { COURSE_STATUS, formatMinutes } from '@/lib/format';
import { useApi, useApiData } from '@/hooks/useApi';
import { useAssignmentActions } from '@/hooks/useAssignmentActions';
import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FormError } from '@/components/ui/Field';
import { Icon } from '@/components/ui/Icon';
import { Modal } from '@/components/ui/Modal';
import { Pill } from '@/components/ui/Pill';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { AssignmentForm } from '@/components/forms/AssignmentForm';
import { CourseForm, type CourseValues } from '@/components/forms/CourseForm';
import { AssignmentRow } from '@/components/courses/AssignmentRow';
import { RiskList } from '@/components/insights/RiskList';

type Editing = { kind: 'new' } | { kind: 'assignment'; assignment: Assignment } | { kind: 'course' } | null;

export default function CourseDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const request = useApi();
  const { setCompleted, remove } = useAssignmentActions();
  const { data, error, loading, reload } = useApiData<CourseDetail>(`/courses/${params.id}`);
  const [editing, setEditing] = useState<Editing>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  if (loading && !data) return <LoadingState label="Loading course" />;
  if (error && !data) return <ErrorState message={error} onRetry={() => reload()} />;
  if (!data) return null;

  const { course, health, assignments, risks, recommended_action } = data;
  const status = COURSE_STATUS[health.status];
  const pending = assignments.filter((a) => !a.completed).sort((a, b) => a.due_date.localeCompare(b.due_date));
  const done = assignments.filter((a) => a.completed).sort((a, b) => b.due_date.localeCompare(a.due_date));

  const run = async (id: string | null, action: () => Promise<unknown>) => {
    setBusyId(id);
    setActionError(null);
    try {
      await action();
      await reload(true);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setBusyId(null);
    }
  };

  const saveAssignment = async (values: AssignmentInput) => {
    if (editing?.kind === 'assignment') await request('PUT', `/assignments/${editing.assignment.id}`, values);
    else await request('POST', '/assignments', values);
    setEditing(null);
    await reload(true);
  };

  const saveCourse = async (values: CourseValues) => {
    await request('PATCH', `/courses/${course.id}`, values);
    setEditing(null);
    await reload(true);
  };

  const deleteAssignment = (a: Assignment) => {
    if (window.confirm(`Delete “${a.title}”? This can’t be undone.`)) run(a.id, () => remove(a.id));
  };

  const deleteCourse = async () => {
    if (!window.confirm(`Delete ${course.name} and all of its assignments? This can’t be undone.`)) return;
    await run(null, () => request('DELETE', `/courses/${course.id}`));
    router.replace('/courses');
  };

  const rows = (list: Assignment[]) => (
    <ul className="divide-y divide-line">
      {list.map((a) => (
        <AssignmentRow
          key={a.id}
          assignment={a}
          busy={busyId === a.id}
          onToggle={() => run(a.id, () => setCompleted(a.id, !a.completed))}
          onEdit={() => setEditing({ kind: 'assignment', assignment: a })}
          onDelete={() => deleteAssignment(a)}
        />
      ))}
    </ul>
  );

  return (
    <div className="animate-fade-up">
      <Link href="/courses" className="mb-4 inline-flex items-center gap-1 text-sm text-muted hover:text-ink">
        <Icon name="chevronLeft" size={16} /> Courses
      </Link>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          {course.code && <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">{course.code}</p>}
          <h1 className="text-[26px] font-semibold tracking-tight md:text-[30px]">{course.name}</h1>
          <div className="mt-2 flex items-center gap-2">
            <Pill tone={status.tone}>{status.label}</Pill>
            <span className="text-sm text-muted">{health.summary}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => setEditing({ kind: 'course' })}>Edit</Button>
          <Button size="sm" onClick={() => setEditing({ kind: 'new' })}>
            <Icon name="plus" size={16} /> Assignment
          </Button>
        </div>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          ['Current grade', health.grade !== null ? `${health.grade.toFixed(1)}%` : 'No grades yet'],
          ['Target', health.target_grade !== null ? `${health.target_grade}%` : 'Not set'],
          ['Work remaining', health.pending_minutes ? formatMinutes(health.pending_minutes) : 'None'],
          ['Completed on time', health.completion_rate !== null ? `${health.completion_rate}%` : '—'],
        ].map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-line bg-surface px-4 py-3.5">
            <p className="text-xs text-muted">{label}</p>
            <p className="mt-1 text-[17px] font-semibold tracking-tight">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Card>
            <CardHeader title="Upcoming" />
            <FormError message={actionError} />
            {pending.length ? rows(pending) : (
              <EmptyState compact title="Nothing pending" body="Add assignments and exams as they’re posted." />
            )}
          </Card>
          {done.length > 0 && (
            <Card>
              <CardHeader title="Completed" />
              {rows(done)}
            </Card>
          )}
        </div>
        <div className="space-y-5">
          <section className="rounded-3xl bg-ink p-5 text-surface">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-surface/60">Recommended next step</p>
            <p className="mt-2 text-[15px] leading-relaxed">{recommended_action}</p>
          </section>
          {risks.length > 0 && (
            <Card>
              <CardHeader title="Risks in this course" />
              <RiskList risks={risks} />
            </Card>
          )}
          <button onClick={deleteCourse} className="text-sm text-muted underline underline-offset-4 hover:text-bad">
            Delete course
          </button>
        </div>
      </div>

      <Modal
        open={editing?.kind === 'new' || editing?.kind === 'assignment'}
        title={editing?.kind === 'assignment' ? 'Edit assignment' : 'Add assignment'}
        onClose={() => setEditing(null)}
      >
        <AssignmentForm
          key={editing?.kind === 'assignment' ? editing.assignment.id : 'new'}
          courses={[course]}
          defaultCourseId={course.id}
          initial={editing?.kind === 'assignment' ? editing.assignment : undefined}
          onSubmit={saveAssignment}
        />
      </Modal>
      <Modal open={editing?.kind === 'course'} title="Edit course" onClose={() => setEditing(null)}>
        <CourseForm initial={course} submitLabel="Save changes" onSubmit={saveCourse} />
      </Modal>
    </div>
  );
}
