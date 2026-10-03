import type { ReactNode } from 'react';
import { Button } from '@/components/ui/Button';

interface StepFrameProps {
  step: number;
  total: number;
  title: string;
  subtitle: string;
  children: ReactNode;
  onBack?: () => void;
  onNext: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  busy?: boolean;
  secondary?: ReactNode;
}

export function StepFrame({
  step, total, title, subtitle, children, onBack, onNext, nextLabel = 'Continue', nextDisabled, busy, secondary,
}: StepFrameProps) {
  return (
    <div className="animate-fade-up" key={step}>
      <div className="mb-8 flex items-center gap-1.5" aria-label={`Step ${step} of ${total}`}>
        {Array.from({ length: total }, (_, i) => (
          <span key={i} className={`h-1 flex-1 rounded-full transition-colors ${i < step ? 'bg-ink' : 'bg-line'}`} />
        ))}
      </div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
        Step {step} of {total}
      </p>
      <h1 className="mt-2 text-[26px] font-semibold tracking-tight sm:text-[30px]">{title}</h1>
      <p className="mt-1.5 text-[15px] text-muted">{subtitle}</p>
      <div className="mt-8">{children}</div>
      <div className="mt-10 flex items-center justify-between gap-3 border-t border-line pt-6">
        {onBack ? (
          <Button variant="ghost" onClick={onBack} disabled={busy}>
            Back
          </Button>
        ) : (
          <span />
        )}
        <div className="flex items-center gap-2">
          {secondary}
          <Button onClick={onNext} loading={busy} disabled={nextDisabled}>
            {nextLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
