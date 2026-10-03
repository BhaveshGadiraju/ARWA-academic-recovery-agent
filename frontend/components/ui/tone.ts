import type { Tone } from '@/lib/format';

export const TONE_TEXT: Record<Tone, string> = {
  good: 'text-good',
  warn: 'text-warn',
  bad: 'text-bad',
  neutral: 'text-muted',
};

export const TONE_SOFT: Record<Tone, string> = {
  good: 'bg-good-soft text-good',
  warn: 'bg-warn-soft text-warn',
  bad: 'bg-bad-soft text-bad',
  neutral: 'bg-sunken text-muted',
};

export const TONE_DOT: Record<Tone, string> = {
  good: 'bg-good',
  warn: 'bg-warn',
  bad: 'bg-bad',
  neutral: 'bg-faint',
};

export const TONE_STROKE: Record<Tone, string> = {
  good: 'var(--color-good)',
  warn: 'var(--color-warn)',
  bad: 'var(--color-bad)',
  neutral: 'var(--color-faint)',
};
