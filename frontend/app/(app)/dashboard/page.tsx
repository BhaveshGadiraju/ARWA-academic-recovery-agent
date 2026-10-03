'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { Dashboard } from '@/lib/types';
import { greeting } from '@/lib/format';
import { useApiData } from '@/hooks/useApi';
import { useProfile } from '@/contexts/ProfileContext';
import { Card, CardHeader } from '@/components/ui/Card';
import { ButtonLink } from '@/components/ui/Button';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { PageHeader } from '@/components/ui/PageHeader';
import { ScoreHero } from '@/components/insights/ScoreHero';
import { TodayStrip } from '@/components/insights/TodayStrip';
import { MetricGrid } from '@/components/insights/MetricGrid';
import { RiskList } from '@/components/insights/RiskList';
import { SetupNudge } from '@/components/insights/SetupNudge';
import { TaskChecklist } from '@/components/tasks/TaskChecklist';
import { FocusSession, type FocusTarget } from '@/components/tasks/FocusSession';
import { PlanTimeline } from '@/components/plan/PlanTimeline';
import { CourseHealthList } from '@/components/courses/CourseHealthList';
import { ArwaCard } from '@/components/arwa/ArwaCard';

const SEE_ALL = 'text-sm font-medium text-muted hover:text-ink';

export default function DashboardPage() {
  const { profile } = useProfile();
  const { data, error, loading, reload } = useApiData<Dashboard>('/dashboard');
  const [focus, setFocus] = useState<FocusTarget | null>(null);

  if (loading && !data) return <LoadingState />;
  if (error && !data) return <ErrorState message={error} onRetry={() => reload()} />;
  if (!data) return null;

  const refresh = () => reload(true);
  const firstName = profile.full_name?.split(' ')[0];
  const today = new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' });

  const startFromInsight = () => {
    const block = data.plan_today?.blocks.find((b) => b.kind === 'study' && b.assignment_id === data.insight.action_assignment_id);
    if (block?.assignment_id) setFocus({ assignmentId: block.assignment_id, title: block.title ?? '', plannedMinutes: block.minutes });
  };

  return (
    <div className="animate-fade-up">
      <PageHeader eyebrow={today} title={`${greeting()}${firstName ? `, ${firstName}` : ''}`} />
      <SetupNudge setup={data.setup} />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ScoreHero score={data.score} trend={data.trend} />
        </div>
        <ArwaCard insight={data.insight} onStart={startFromInsight} />

        <div className="lg:col-span-3">
          <TodayStrip today={data.today} />
        </div>

        <div className="space-y-5 lg:col-span-2">
          <Card>
            <CardHeader title="Today’s priorities" action={<Link href="/plan" className={SEE_ALL}>Full plan</Link>} />
            {data.priorities.length ? (
              <TaskChecklist items={data.priorities} onChanged={refresh} />
            ) : (
              <EmptyState
                compact
                title="Nothing pending"
                body={data.setup.has_courses ? 'Add new assignments as they’re posted.' : 'Add courses and assignments to get priorities.'}
                action={<ButtonLink href="/courses" variant="secondary" size="sm">Add assignments</ButtonLink>}
              />
            )}
          </Card>

          <Card>
            <CardHeader title="Today’s plan" eyebrow={data.plan_today?.label} />
            {data.plan_today ? (
              <PlanTimeline day={data.plan_today} onStart={setFocus} />
            ) : (
              <EmptyState compact title="No plan yet" body="Set your weekly study time so ARWA can schedule your work." />
            )}
          </Card>
        </div>

        <div className="space-y-5">
          <Card>
            <CardHeader title="Risks" />
            {data.risks.length ? (
              <RiskList risks={data.risks} limit={4} />
            ) : (
              <EmptyState compact title="No risks detected" body="Nothing is at risk right now. Nice work." />
            )}
          </Card>
          <Card>
            <CardHeader title="Course health" action={<Link href="/courses" className={SEE_ALL}>All</Link>} />
            {data.courses.length ? (
              <CourseHealthList courses={data.courses} />
            ) : (
              <EmptyState compact title="No courses yet" body="Add your courses to see their health." />
            )}
          </Card>
        </div>

        <div className="lg:col-span-3">
          <MetricGrid metrics={data.metrics} />
        </div>
      </div>

      <FocusSession target={focus} onClose={() => setFocus(null)} onLogged={refresh} />
    </div>
  );
}
