import type { TrendPoint } from '@/lib/types';
import { formatShortDate } from '@/lib/format';

interface TrendChartProps {
  points: TrendPoint[];
  height?: number;
  showLabels?: boolean;
  emptyText?: string;
}

/** Minimal 0–100 line. Shows a friendly note until there are two points. */
export function TrendChart({
  points, height = 64, showLabels = false, emptyText = 'Your trend appears after a second day of check-ins.',
}: TrendChartProps) {
  if (points.length < 2) {
    return <p className="text-xs text-faint">{emptyText}</p>;
  }
  const width = 300;
  const pad = 4;
  const x = (i: number) => pad + (i * (width - pad * 2)) / (points.length - 1);
  const y = (score: number) => pad + ((100 - score) / 100) * (height - pad * 2);
  const path = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.score).toFixed(1)}`).join(' ');
  const area = `${path} L${x(points.length - 1)},${height} L${x(0)},${height} Z`;
  const last = points[points.length - 1];

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full overflow-visible" preserveAspectRatio="none" style={{ height }} role="img" aria-label="Recovery Score trend">
        <path d={area} fill="var(--color-sunken)" opacity="0.8" />
        <path d={path} fill="none" stroke="var(--color-ink)" strokeWidth="1.8" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
        <circle cx={x(points.length - 1)} cy={y(last.score)} r="3.5" fill="var(--color-ink)" />
      </svg>
      {showLabels && (
        <div className="mt-2 flex justify-between text-[11px] text-faint">
          <span>{formatShortDate(points[0].date)}</span>
          <span>{formatShortDate(last.date)}</span>
        </div>
      )}
    </div>
  );
}
