import { scoreTone } from '@/lib/format';
import { TONE_STROKE } from '@/components/ui/tone';

interface ScoreRingProps {
  score: number | null;
  label: string;
  size?: number;
}

/** The Recovery Score as a ring. Colour reflects the band; the arc animates in. */
export function ScoreRing({ score, label, size = 216 }: ScoreRingProps) {
  const stroke = Math.round(size * 0.07);
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = score === null ? 0 : Math.max(0, Math.min(100, score)) / 100;
  const color = TONE_STROKE[scoreTone(score)];

  return (
    <div className="relative" style={{ width: size, height: size }} role="img" aria-label={`Recovery Score ${score ?? 'not available'}: ${label}`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--color-sunken)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - progress)}
          style={{ transition: 'stroke-dashoffset 1.1s cubic-bezier(0.2, 0.7, 0.2, 1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-semibold tabular-nums tracking-tight" style={{ fontSize: size * 0.3, lineHeight: 1 }}>
          {score ?? '—'}
        </span>
        <span className="mt-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{label}</span>
      </div>
    </div>
  );
}
