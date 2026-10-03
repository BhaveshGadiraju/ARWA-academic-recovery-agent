'use client';

import { useState } from 'react';
import type { CourseHealth } from '@/lib/types';
import { useApi, useApiData } from '@/hooks/useApi';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Modal } from '@/components/ui/Modal';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { PageHeader } from '@/components/ui/PageHeader';
import { CourseForm, type CourseValues } from '@/components/forms/CourseForm';
import { CourseHealthList } from '@/components/courses/CourseHealthList';

export default function CoursesPage() {
  const request = useApi();
  const { data: courses, error, loading, reload } = useApiData<CourseHealth[]>('/courses/health');
  const [adding, setAdding] = useState(false);

  const addCourse = async (values: CourseValues) => {
    await request('POST', '/courses', values);
    setAdding(false);
    await reload(true);
  };

  if (loading && !courses) return <LoadingState label="Loading your courses" />;
  if (error && !courses) return <ErrorState message={error} onRetry={() => reload()} />;
  if (!courses) return null;

  return (
    <div className="animate-fade-up">
      <PageHeader
        title="Courses"
        subtitle="Grades, workload, and what’s next in each class. Open a course to manage its assignments."
        action={
          <Button size="sm" onClick={() => setAdding(true)}>
            <Icon name="plus" size={16} /> Add course
          </Button>
        }
      />
      <Card>
        {courses.length ? (
          <CourseHealthList courses={courses} detailed />
        ) : (
          <EmptyState
            title="No courses yet"
            body="Add the courses you’re taking this term to start tracking their health."
            action={<Button onClick={() => setAdding(true)}>Add your first course</Button>}
          />
        )}
      </Card>
      <Modal open={adding} title="Add course" onClose={() => setAdding(false)}>
        <CourseForm onSubmit={addCourse} submitLabel="Add course" />
      </Modal>
    </div>
  );
}
