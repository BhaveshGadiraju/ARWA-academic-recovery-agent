import Link from 'next/link';
import type { Dashboard } from '@/lib/types';
import { Icon } from '@/components/ui/Icon';

/** Tells the student exactly which missing data limits the analysis. */
export function SetupNudge({ setup }: { setup: Dashboard['setup'] }) {
  const missing = [
    !setup.has_courses && { text: 'Add your courses', href: '/courses' },
    setup.has_courses && !setup.has_assignments && { text: 'Add upcoming assignments and exams', href: '/courses' },
    !setup.has_availability && { text: 'Set your weekly study time', href: '/settings' },
    setup.has_assignments && !setup.has_grades && { text: 'Add points to graded work so ARWA can track grades', href: '/courses' },
  ].filter(Boolean) as { text: string; href: string }[];

  if (!missing.length) return null;
  return (
    <div className="mb-6 rounded-2xl border border-warn/25 bg-warn-soft/60 px-4 py-3">
      <p className="text-sm font-medium text-ink">ARWA needs a bit more to give you a complete picture:</p>
      <ul className="mt-1.5 flex flex-wrap gap-x-5 gap-y-1">
        {missing.map((m) => (
          <li key={m.text}>
            <Link href={m.href} className="inline-flex items-center gap-1 text-sm text-ink-soft underline underline-offset-4 hover:text-ink">
              {m.text} <Icon name="chevronRight" size={14} />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
