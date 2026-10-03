import type { ReactNode } from 'react';
import { Button } from './Button';

export function LoadingState({ label = 'ARWA is analyzing your semester' }: { label?: string }) {
  return (
    <div role="status" className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <div className="relative h-14 w-14">
        <span className="absolute inset-0 rounded-full border-[3px] border-line" />
        <span className="absolute inset-0 animate-spin rounded-full border-[3px] border-ink border-r-transparent border-b-transparent" />
      </div>
      <p className="animate-pulse-soft text-[11px] font-semibold uppercase tracking-[0.18em] text-muted">{label}…</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="mx-auto flex max-w-sm flex-col items-center gap-3 py-20 text-center">
      <p className="text-[15px] font-medium text-ink">We hit a snag</p>
      <p className="text-sm text-muted">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  body: string;
  action?: ReactNode;
  compact?: boolean;
}

export function EmptyState({ title, body, action, compact }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center gap-2 text-center ${compact ? 'py-6' : 'py-14'}`}>
      <p className="text-[15px] font-medium text-ink">{title}</p>
      <p className="max-w-xs text-sm text-muted">{body}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
