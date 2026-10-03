import type { ReactNode } from 'react';
import type { Tone } from '@/lib/format';
import { TONE_DOT, TONE_SOFT } from './tone';

export function Pill({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${TONE_SOFT[tone]}`}>
      {children}
    </span>
  );
}

export function Dot({ tone = 'neutral', className = '' }: { tone?: Tone; className?: string }) {
  return <span aria-hidden className={`inline-block h-2 w-2 shrink-0 rounded-full ${TONE_DOT[tone]} ${className}`} />;
}
