import Link from 'next/link';
import type { CourseHealth } from '@/lib/types';
import { COURSE_STATUS, formatDueInline } from '@/lib/format';
import { Dot, Pill } from '@/components/ui/Pill';
import { Icon } from '@/components/ui/Icon';

/** Courses with grade, health status, and the next deadline. Each row links to the course page. */
export function CourseHealthList({ courses, detailed = false }: { courses: CourseHealth[]; detailed?: boolean }) {
  return (
    <ul className="divide-y divide-line">
      {courses.map((c) => {
        const status = COURSE_STATUS[c.status];
        return (
          <li key={c.course_id}>
            <Link href={`/courses/${c.course_id}`} className="group flex items-center gap-4 py-3.5 first:pt-0">
              <Dot tone={status.tone} />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline gap-2">
                  <p className="truncate text-[15px] font-medium">{c.code || c.name}</p>
                  {c.code && <p className="hidden truncate text-[13px] text-faint sm:block">{c.name}</p>}
                </div>
                <p className="truncate text-[13px] text-muted">
                  {c.summary}
                  {detailed && c.next_due ? ` · Next: ${c.next_due.title} (${formatDueInline(c.next_due.due_date)})` : ''}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                {c.grade !== null ? (
                  <span className="text-[15px] font-semibold tabular-nums">{Math.round(c.grade)}%</span>
                ) : (
                  <span className="text-xs text-faint">No grade</span>
                )}
                {detailed && <Pill tone={status.tone}>{status.label}</Pill>}
                <Icon name="chevronRight" size={16} className="text-faint transition-transform group-hover:translate-x-0.5" />
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
