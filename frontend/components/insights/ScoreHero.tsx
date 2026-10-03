'use client';

import { useState } from 'react';
import type { RecoveryScore, TrendPoint } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Icon } from '@/components/ui/Icon';
import { ScoreRing } from './ScoreRing';
import { TrendChart } from './TrendChart';
import { ScoreFactors } from './ScoreFactors';

function Delta({ delta }: { delta: number | null }) {
  if (delta === null) return null;
  const tone = delta > 0 ? 'text-good' : delta < 0 ? 'text-bad' : 'text-muted';
  const text = delta === 0 ? 'Same as yesterday' : `${delta > 0 ? '+' : ''}${delta} since last check-in`;
  return <span className={`text-sm font-medium ${tone}`}>{text}</span>;
}

export function ScoreHero({ score, trend }: { score: RecoveryScore; trend: TrendPoint[] }) {
  const [showWhy, setShowWhy] = useState(false);

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-col items-center gap-8 md:flex-row md:items-center md:gap-12">
        <ScoreRing score={score.score} label={score.band_label} />
        <div className="w-full flex-1 text-center md:text-left">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">Recovery Score</p>
          <p className="mt-2 text-[19px] font-medium leading-snug tracking-tight text-ink">{score.headline}</p>
          <div className="mt-3">
            <Delta delta={score.delta} />
          </div>
          {score.score !== null && (
            <div className="mt-5 md:max-w-sm">
              <TrendChart points={trend} />
            </div>
          )}
          {score.factors.length > 0 && (
            <button
              onClick={() => setShowWhy((v) => !v)}
              aria-expanded={showWhy}
              className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-ink-soft hover:text-ink"
            >
              {showWhy ? 'Hide breakdown' : 'Why this score?'}
              <Icon name="chevronRight" size={16} className={`transition-transform ${showWhy ? 'rotate-90' : ''}`} />
            </button>
          )}
        </div>
      </div>
      {showWhy && <ScoreFactors factors={score.factors} />}
    </Card>
  );
}
