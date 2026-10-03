import type { ScoreFactor } from '@/lib/types';
import { Dot } from '@/components/ui/Pill';

const IMPACT_TONE = { positive: 'good', negative: 'bad', neutral: 'neutral' } as const;

/** Transparent breakdown: each factor, its weight, and the points it costs. */
export function ScoreFactors({ factors }: { factors: ScoreFactor[] }) {
  return (
    <div className="mt-6 animate-fade-up border-t border-line pt-5">
      <ul className="space-y-3">
        {factors.map((f) => (
          <li key={f.key} className="flex items-start gap-3">
            <Dot tone={IMPACT_TONE[f.impact]} className="mt-1.5" />
            <div className="flex-1">
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-sm font-medium">{f.label}</p>
                <p className="shrink-0 text-xs tabular-nums text-muted">
                  {f.points_lost > 0 ? `−${f.points_lost} pts` : 'no penalty'}
                  {f.weight > 0 && ` · ${Math.round(f.weight * 100)}% weight`}
                </p>
              </div>
              <p className="mt-0.5 text-[13px] text-muted">{f.detail}</p>
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-5 text-xs text-faint">
        The Recovery Score is ARWA&apos;s planning metric: grades 30%, completion 20%, time capacity 30%, deadline headroom 20%,
        minus 5 points per overdue item (max 15). It isn&apos;t a clinical or scientifically validated measure.
      </p>
    </div>
  );
}
