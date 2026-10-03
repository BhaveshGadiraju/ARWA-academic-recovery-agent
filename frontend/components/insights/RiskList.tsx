import type { Risk } from '@/lib/types';
import { SEVERITY_TONE } from '@/lib/format';
import { Pill } from '@/components/ui/Pill';

const SEVERITY_LABEL = { critical: 'Critical', high: 'High', moderate: 'Moderate', low: 'Low' } as const;

/** Deterministic risks: what, why, and the next step. */
export function RiskList({ risks, limit }: { risks: Risk[]; limit?: number }) {
  const shown = limit ? risks.slice(0, limit) : risks;
  return (
    <ul className="space-y-3">
      {shown.map((risk) => (
        <li key={risk.id} className="rounded-2xl border border-line bg-canvas/50 p-4">
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm font-semibold">{risk.title}</p>
            <Pill tone={SEVERITY_TONE[risk.severity]}>{SEVERITY_LABEL[risk.severity]}</Pill>
          </div>
          {risk.course_name && <p className="mt-0.5 text-xs text-faint">{risk.course_name}</p>}
          <p className="mt-2 text-[13px] text-muted">{risk.reason}</p>
          <p className="mt-2 text-[13px] font-medium text-ink-soft">→ {risk.action}</p>
        </li>
      ))}
    </ul>
  );
}
