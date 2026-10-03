'use client';

import type { Course } from '@/lib/types';
import { useApi } from '@/hooks/useApi';
import { CourseForm, type CourseValues } from '@/components/forms/CourseForm';
import { ItemList } from './ItemList';
import { StepFrame } from './StepFrame';

interface Props {
  courses: Course[];
  onChange: (courses: Course[]) => void;
  onBack: () => void;
  onNext: () => void;
}

export function CoursesStep({ courses, onChange, onBack, onNext }: Props) {
  const request = useApi();

  const add = async (values: CourseValues) => {
    const course = await request<Course>('POST', '/courses', values);
    onChange([...courses, course]);
  };

  const remove = async (id: string) => {
    await request('DELETE', `/courses/${id}`);
    onChange(courses.filter((c) => c.id !== id));
  };

  return (
    <StepFrame
      step={2}
      total={5}
      title="What are you taking?"
      subtitle="Add each course this term. A target grade helps ARWA spot courses that need attention."
      onBack={onBack}
      onNext={onNext}
      nextDisabled={!courses.length}
    >
      <ItemList
        items={courses.map((c) => ({
          id: c.id,
          title: c.code ? `${c.code} · ${c.name}` : c.name,
          meta: `${c.credits} credits${c.target_grade != null ? ` · target ${c.target_grade}%` : ''}`,
        }))}
        onRemove={remove}
        empty="No courses yet. Add your first one below."
      />
      <div className="mt-6 rounded-2xl bg-sunken/60 p-4 sm:p-5">
        <CourseForm onSubmit={add} />
      </div>
    </StepFrame>
  );
}
