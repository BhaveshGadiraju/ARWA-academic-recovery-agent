'use client';

import { useState } from 'react';
import type { PriorityItem } from '@/lib/types';
import { CATEGORY_LABEL, formatDue, formatMinutes } from '@/lib/format';
import { useAssignmentActions } from '@/hooks/useAssignmentActions';
import { FormError } from '@/components/ui/Field';
import { CheckButton } from './CheckButton';

interface Props {
  items: PriorityItem[];
  onChanged: () => void;
}

/** Today's priorities as a checklist. Checking an item marks the assignment complete. */
export function TaskChecklist({ items, onChanged }: Props) {
  const { setCompleted } = useAssignmentActions();
  const [done, setDone] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const toggle = async (item: PriorityItem) => {
    const completed = !done.has(item.assignment_id);
    setBusy(item.assignment_id);
    setError(null);
    try {
      await setCompleted(item.assignment_id, completed);
      setDone((prev) => {
        const next = new Set(prev);
        if (completed) next.add(item.assignment_id);
        else next.delete(item.assignment_id);
        return next;
      });
      setTimeout(onChanged, 700);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update that task.');
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <ul className="divide-y divide-line">
        {items.map((item) => {
          const checked = done.has(item.assignment_id);
          const overdue = item.days_until_due < 0;
          return (
            <li key={item.assignment_id} className="flex items-start gap-3.5 py-3.5 first:pt-0 last:pb-0">
              <div className="pt-0.5">
                <CheckButton
                  checked={checked}
                  busy={busy === item.assignment_id}
                  label={`Mark ${item.title} complete`}
                  onToggle={() => toggle(item)}
                />
              </div>
              <div className={`min-w-0 flex-1 transition-opacity ${checked ? 'opacity-45' : ''}`}>
                <p className={`text-[15px] font-medium ${checked ? 'line-through decoration-faint' : ''}`}>{item.title}</p>
                <p className="mt-0.5 text-[13px] text-muted">
                  {[item.course_name, CATEGORY_LABEL[item.category], formatMinutes(item.remaining_minutes) + ' left'].filter(Boolean).join(' · ')}
                </p>
                <p className="mt-1 text-xs text-faint">{item.reason}</p>
              </div>
              <span className={`shrink-0 text-xs font-medium ${overdue ? 'text-bad' : item.days_until_due <= 1 ? 'text-warn' : 'text-muted'}`}>
                {formatDue(item.due_date)}
              </span>
            </li>
          );
        })}
      </ul>
      <div className="mt-3">
        <FormError message={error} />
      </div>
    </div>
  );
}
