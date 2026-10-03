'use client';

import { useState } from 'react';
import type { RecoveryPlan } from '@/lib/types';
import { formatDueInline, formatMinutes, formatShortDate } from '@/lib/format';
import { useApiData } from '@/hooks/useApi';
import { Card } from '@/components/ui/Card';
import { ButtonLink } from '@/components/ui/Button';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { PageHeader } from '@/components/ui/PageHeader';
import { Icon } from '@/components/ui/Icon';
import { PlanTimeline } from '@/components/plan/PlanTimeline';
import { FocusSession, type FocusTarget } from '@/components/tasks/FocusSession';

function UnscheduledWarning({ plan }: { plan: RecoveryPlan }) {
  if (!plan.unscheduled.length) return null;
  return (
    <div className="mb-6 rounded-2xl border border-bad/20 bg-bad-soft/60 p-4">
      <p className="flex items-center gap-2 text-sm font-semibold text-bad">
        <Icon name="alert" size={17} /> Some work doesn’t fit before it’s due
      </p>
      <ul className="mt-2 space-y-1 text-sm text-ink-soft">
        {plan.unscheduled.map((u) => (
          <li key={u.assignment_id}>
            <span className="font-medium">{u.title}</span>
            {u.course_name && <span className="text-muted"> · {u.course_name}</span>} needs {formatMinutes(u.unscheduled_minutes)} more (
            {formatDueInline(u.due_date)})
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[13px] text-muted">
        Add study time before these deadlines, cut scope, or talk to your instructor early. ARWA won’t pretend it fits.
      </p>
    </div>
  );
}

export default function PlanPage() {
  const { data: plan, error, loading, reload } = useApiData<RecoveryPlan>('/plan?days=7');
  const [focus, setFocus] = useState<FocusTarget | null>(null);

  if (loading && !plan) return <LoadingState label="ARWA is building your plan" />;
  if (error && !plan) return <ErrorState message={error} onRetry={() => reload()} />;
  if (!plan) return null;

  const hasBlocks = plan.days.some((d) => d.blocks.length);
  const hasTime = plan.days.some((d) => d.window_minutes > 0);

  return (
    <div className="animate-fade-up">
      <PageHeader
        title="Recovery plan"
        subtitle={
          hasBlocks
            ? `${formatMinutes(plan.planned_minutes)} scheduled over the next 7 days · ${plan.is_feasible ? 'everything fits' : 'some work doesn’t fit'}`
            : 'Your next 7 days, built from your real assignments and study time.'
        }
        action={<ButtonLink href="/settings" variant="secondary" size="sm">Edit study time</ButtonLink>}
      />
      <UnscheduledWarning plan={plan} />

      {!hasTime ? (
        <Card>
          <EmptyState
            title="No study time set"
            body="ARWA only schedules work inside the hours you say you have. Add your weekly study time to get a plan."
            action={<ButtonLink href="/settings">Set study time</ButtonLink>}
          />
        </Card>
      ) : !hasBlocks && !plan.unscheduled.length ? (
        <Card>
          <EmptyState
            title="You’re all caught up"
            body="No incomplete assignments to schedule. Add new work as it’s assigned."
            action={<ButtonLink href="/courses" variant="secondary">Add assignments</ButtonLink>}
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {plan.days.map((day) => (
            <Card key={day.date} as="article">
              <div className="mb-4 flex items-baseline justify-between">
                <div>
                  <h2 className="text-[17px] font-semibold tracking-tight">{day.label}</h2>
                  <p className="text-xs text-faint">{formatShortDate(day.date)}</p>
                </div>
                <p className="text-xs text-muted">
                  {formatMinutes(day.study_minutes)} of {formatMinutes(day.window_minutes)}
                </p>
              </div>
              <PlanTimeline day={day} onStart={setFocus} />
            </Card>
          ))}
        </div>
      )}

      <FocusSession target={focus} onClose={() => setFocus(null)} onLogged={() => reload(true)} />
    </div>
  );
}
