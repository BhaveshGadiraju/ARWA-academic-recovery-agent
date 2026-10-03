import { Icon } from '@/components/ui/Icon';

interface CheckButtonProps {
  checked: boolean;
  busy?: boolean;
  label: string;
  onToggle: () => void;
}

/** Round checkbox with a small pop animation when completed. */
export function CheckButton({ checked, busy, label, onToggle }: CheckButtonProps) {
  return (
    <button
      role="checkbox"
      aria-checked={checked}
      aria-label={label}
      disabled={busy}
      onClick={onToggle}
      className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-[1.5px] transition-colors ${
        checked ? 'border-good bg-good text-surface' : 'border-line-strong hover:border-ink'
      } ${busy ? 'opacity-60' : ''}`}
    >
      {checked && <Icon name="check" size={14} className="animate-check" />}
    </button>
  );
}
