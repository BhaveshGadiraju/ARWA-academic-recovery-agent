'use client';

import type { Progress } from '@/lib/types';
import { formatDue, formatMinutes, formatShortDate } from '@/lib/format';
import { useApiData } from '@/hooks/useApi';
import { Card, CardHeader } from '@/components/ui/Card';
import { Pill } from '@/components/ui/Pill';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { PageHeader } from '@/components/ui/PageHeader';
import { TrendChart } from '@/components/insights/TrendChart';
import { StudyBars } from '@/components/progress/StudyBars';
import { WeeklyCompletion } from '@/components/progress/WeeklyCompletion';

export default function ProgressPage() {
  const { data, error, loading, reload } = useApiData<Progress>('/progress');

  if (loading && !data) return <LoadingState label="Loading your progress" />;
  if (error && !data) return <ErrorState message={error} onRetry={() => reload()} />;
  if (!data) return null;

  const { totals } = data;
  const stats = [
    ['Completed', String(totals.completed ?? 0)],
    ['Still to do', String(totals.pending ?? 0)],
    ['Studied this week', formatMinutes(totals.studied_minutes_this_week ?? 0)],
    ['Overdue', String(totals.overdue ?? 0)],
  ];
  const gradedCourses = data.course_trends.filter((c) => c.points.length);

  return (
    <div className="animate-fade-up">
      <PageHeader title="Progress" subtitle="How your semester is moving: score, study time, and completed work." />

      <div className="mb-5 grid grid-cols-2 gap-3 md:grid-cols-4">
        {stats.map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-line bg-surface px-4 py-3.5">
            <p className="text-xs text-muted">{label}</p>
            <p className="mt-1 text-[22px] font-semibold tabular-nums tracking-tight">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader title="Recovery Score" eyebrow="Last 30 days" />
          <TrendChart points={data.score_history} height={140} showLabels />
        </Card>
        <Card>
          <CardHeader title="Study time" eyebrow="Last 14 days" />
          {data.study_days.some((d) => d.studied_minutes > 0) ? (
            <StudyBars days={data.study_days} />
          ) : (
            <EmptyState compact title="No study sessions yet" body="Press Start on a plan block to time a session. It’s logged here." />
          )}
        </Card>
        <Card>
          <CardHeader title="Completed per week" />
          <WeeklyCompletion weeks={data.weekly_completion} />
          <div className="mt-3 flex gap-4 text-xs text-muted">
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-good" /> On time</span>
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-warn" /> Late</span>
          </div>
        </Card>
        <Card>
          <CardHeader title="Missed & late work" />
          {data.missed.length ? (
            <ul className="divide-y divide-line">
              {data.missed.slice(0, 8).map((m) => (
                <li key={m.assignment_id} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{m.title}</p>
                    <p className="text-xs text-muted">
                      {m.course_name} · {m.status === 'overdue' ? formatDue(m.due_date) : `Due ${formatShortDate(m.due_date)}`}
                    </p>
                  </div>
                  <Pill tone={m.status === 'overdue' ? 'bad' : 'warn'}>{m.status === 'overdue' ? 'Overdue' : 'Late'}</Pill>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState compact title="Nothing missed" body="No overdue or late work in the last 30 days." />
          )}
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title="Grade trends" />
          {gradedCourses.length ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {gradedCourses.map((c) => {
                const last = c.points[c.points.length - 1];
                return (
                  <div key={c.course_id}>
                    <div className="mb-2 flex items-baseline justify-between">
                      <p className="text-sm font-medium">{c.name}</p>
                      <p className="text-sm font-semibold tabular-nums">{last.grade}%</p>
                    </div>
                    <TrendChart
                      points={c.points.map((p) => ({ date: p.date, score: p.grade }))}
                      height={56}
                      emptyText="Trend appears after a second graded item."
                    />
                  </div>
                );
              })}
            </div>
          ) : (
            <EmptyState compact title="No grades yet" body="Add points to graded assignments to see how each course is trending." />
          )}
        </Card>
      </div>
    </div>
  );
}
