'use client';

import type { Assignment, AssignmentInput, Course } from '@/lib/types';
import { useApi } from '@/hooks/useApi';
import { CATEGORY_LABEL, formatDue } from '@/lib/format';
import { AssignmentForm } from '@/components/forms/AssignmentForm';
import { ItemList } from './ItemList';
import { StepFrame } from './StepFrame';

interface Props {
  courses: Course[];
  assignments: Assignment[];
  onChange: (assignments: Assignment[]) => void;
  onBack: () => void;
  onNext: () => void;
}

export function AssignmentsStep({ courses, assignments, onChange, onBack, onNext }: Props) {
  const request = useApi();

  const add = async (values: AssignmentInput) => {
    const created = await request<Assignment>('POST', '/assignments', values);
    onChange([...assignments, created]);
  };

  const remove = async (id: string) => {
    await request('DELETE', `/assignments/${id}`);
    onChange(assignments.filter((a) => a.id !== id));
  };

  return (
    <StepFrame
      step={3}
      total={5}
      title="What’s coming up?"
      subtitle="Add upcoming assignments and exams. Add graded work with points too, so ARWA knows your current grades."
      onBack={onBack}
      onNext={onNext}
      nextLabel={assignments.length ? 'Continue' : 'Skip for now'}
    >
      <ItemList
        items={assignments.map((a) => ({
          id: a.id,
          title: a.title,
          meta: `${a.course_code || a.course} · ${CATEGORY_LABEL[a.category]} · ${
            a.points_earned != null ? `${a.points_earned}/${a.points_possible} pts` : formatDue(a.due_date)
          }`,
        }))}
        onRemove={remove}
        empty="Nothing added yet. Start with whatever is due soonest."
      />
      <div className="mt-6 rounded-2xl bg-sunken/60 p-4 sm:p-5">
        <AssignmentForm courses={courses} onSubmit={add} />
      </div>
    </StepFrame>
  );
}
