import type { Assignment } from '@/lib/types';
import { CATEGORY_LABEL, daysFromToday, formatDue, formatShortDate } from '@/lib/format';
import { Icon } from '@/components/ui/Icon';
import { CheckButton } from '@/components/tasks/CheckButton';

interface Props {
  assignment: Assignment;
  busy: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function gradeText(a: Assignment): string | null {
  if (a.points_earned == null || !a.points_possible) return null;
  return `${a.points_earned}/${a.points_possible} · ${Math.round((100 * a.points_earned) / a.points_possible)}%`;
}

export function AssignmentRow({ assignment: a, busy, onToggle, onEdit, onDelete }: Props) {
  const overdue = !a.completed && daysFromToday(a.due_date) < 0;
  const grade = gradeText(a);
  return (
    <li className="flex items-center gap-3.5 py-3">
      <CheckButton checked={a.completed} busy={busy} label={`Mark ${a.title} ${a.completed ? 'incomplete' : 'complete'}`} onToggle={onToggle} />
      <div className={`min-w-0 flex-1 ${a.completed ? 'opacity-55' : ''}`}>
        <p className={`truncate text-[15px] font-medium ${a.completed ? 'line-through decoration-faint' : ''}`}>{a.title}</p>
        <p className="truncate text-[13px] text-muted">
          {CATEGORY_LABEL[a.category]} · {a.estimated_hours}h ·{' '}
          <span className={overdue ? 'font-medium text-bad' : ''}>
            {a.completed ? `Due ${formatShortDate(a.due_date)}` : formatDue(a.due_date)}
          </span>
        </p>
      </div>
      {grade && <span className="hidden shrink-0 text-[13px] font-medium tabular-nums sm:inline">{grade}</span>}
      <div className="flex shrink-0">
        <button onClick={onEdit} aria-label={`Edit ${a.title}`} className="rounded-full p-2 text-faint hover:bg-sunken hover:text-ink">
          <Icon name="edit" size={16} />
        </button>
        <button onClick={onDelete} aria-label={`Delete ${a.title}`} className="rounded-full p-2 text-faint hover:bg-sunken hover:text-bad">
          <Icon name="trash" size={16} />
        </button>
      </div>
    </li>
  );
}
