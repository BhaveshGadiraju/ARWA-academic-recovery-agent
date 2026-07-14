'use client';

import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'accent' | 'muted';
}

export function StatsCard({
  title,
  value,
  description,
  icon,
  variant = 'default',
}: StatsCardProps) {
  const variantStyles = {
    default: 'bg-card hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-300',
    accent: 'bg-gradient-to-br from-primary/8 to-primary/3 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-300',
    muted: 'bg-muted/40 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-300',
  };

  return (
    <Card className={cn('rounded-2xl p-8', variantStyles[variant])}>
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-3 flex-1">
          <p className="text-sm font-semibold text-foreground/70 tracking-wide uppercase">{title}</p>
          <p className="text-5xl font-bold text-foreground tracking-tight">{value}</p>
          {description && (
            <p className="text-sm text-foreground/60 font-medium">{description}</p>
          )}
        </div>
        {icon && (
          <div className={cn(
            'h-14 w-14 rounded-xl flex items-center justify-center flex-shrink-0',
            variant === 'accent' ? 'bg-primary/12 text-primary' : 'bg-muted/60 text-foreground/70'
          )}>
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}
