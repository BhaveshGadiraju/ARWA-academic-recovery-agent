import type { Category, CourseStatus, Severity } from './types';

/** Parse a YYYY-MM-DD date as a local calendar date (no timezone shift). */
export function parseDate(value: string): Date {
  const [y, m, d] = value.slice(0, 10).split('-').map(Number);
  return new Date(y, m - 1, d);
}

export function toISODate(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function addDays(date: Date, days: number): Date {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
}

export function daysFromToday(value: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((parseDate(value).getTime() - today.getTime()) / 86_400_000);
}

export function formatDue(value: string): string {
  const days = daysFromToday(value);
  if (days < -1) return `${-days} days overdue`;
  if (days === -1) return 'Due yesterday';
  if (days === 0) return 'Due today';
  if (days === 1) return 'Due tomorrow';
  if (days < 7) return `Due ${parseDate(value).toLocaleDateString(undefined, { weekday: 'long' })}`;
  return `Due ${formatShortDate(value)}`;
}

/** formatDue for use mid-sentence: "due Sunday", not "due sunday". */
export function formatDueInline(value: string): string {
  const label = formatDue(value);
  return label[0].toLowerCase() + label.slice(1);
}

export function formatShortDate(value: string): string {
  return parseDate(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}

/** "18:05" -> "6:05 PM" */
export function formatClock(hhmm: string): string {
  const [h, m] = hhmm.split(':').map(Number);
  const suffix = h >= 12 ? 'PM' : 'AM';
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${suffix}`;
}

export function greeting(now = new Date()): string {
  const hour = now.getHours();
  if (hour < 4) return 'Good evening';
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

export const CATEGORY_LABEL: Record<Category, string> = {
  homework: 'Homework',
  exam: 'Exam',
  quiz: 'Quiz',
  project: 'Project',
  lab: 'Lab',
  reading: 'Reading',
  paper: 'Paper',
  other: 'Other',
};

export type Tone = 'good' | 'warn' | 'bad' | 'neutral';

export const SEVERITY_TONE: Record<Severity, Tone> = {
  critical: 'bad',
  high: 'bad',
  moderate: 'warn',
  low: 'neutral',
};

export const COURSE_STATUS: Record<CourseStatus, { label: string; tone: Tone }> = {
  on_track: { label: 'On track', tone: 'good' },
  watch: { label: 'Watch', tone: 'warn' },
  at_risk: { label: 'At risk', tone: 'bad' },
  no_data: { label: 'No grades yet', tone: 'neutral' },
};

export function scoreTone(score: number | null): Tone {
  if (score === null) return 'neutral';
  if (score >= 65) return 'good';
  if (score >= 45) return 'warn';
  return 'bad';
}

export const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
