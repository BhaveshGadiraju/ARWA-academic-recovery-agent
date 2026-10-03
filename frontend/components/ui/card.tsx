import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  as?: 'section' | 'div' | 'article';
}

export function Card({ children, className = '', as: Tag = 'section' }: CardProps) {
  return (
    <Tag className={`rounded-3xl border border-line bg-surface p-5 shadow-card sm:p-6 ${className}`}>{children}</Tag>
  );
}

interface CardHeaderProps {
  title: string;
  eyebrow?: string;
  action?: ReactNode;
}

export function CardHeader({ title, eyebrow, action }: CardHeaderProps) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div>
        {eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}
        <h2 className="text-[17px] font-semibold tracking-tight text-ink">{title}</h2>
      </div>
      {action}
    </div>
  );
}

export function Eyebrow({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <p className={`mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-faint ${className}`}>{children}</p>
  );
}
