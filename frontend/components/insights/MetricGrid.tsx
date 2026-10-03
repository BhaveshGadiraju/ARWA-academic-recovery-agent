import type { Metric } from '@/lib/types';
import type { Tone } from '@/lib/format';
import { Card, CardHeader } from '@/components/ui/Card';
import { TONE_DOT, TONE_TEXT } from '@/components/ui/tone';

function metricTone(metric: Metric): Tone {
  if (metric.value === null) return 'neutral';
  const goodness = metric.higher_is_better ? metric.value : 100 - metric.value;
  if (goodness >= 65) return 'good';
  if (goodness >= 40) return 'warn';
  return 'bad';
}

/** Academic Health: workload, deadline pressure, performance, capacity. */
export function MetricGrid({ metrics }: { metrics: Metric[] }) {
  return (
    <Card>
      <CardHeader title="Academic health" />
      <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
        {metrics.map((m) => {
          const tone = metricTone(m);
          return (
            <div key={m.key} title={m.meaning}>
              <div className="flex items-baseline justify-between">
                <p className="text-sm font-medium">{m.label}</p>
                <p className={`text-sm font-semibold ${TONE_TEXT[tone]}`}>{m.level}</p>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-sunken">
                <div
                  className={`h-full rounded-full ${TONE_DOT[tone]} transition-[width] duration-700`}
                  style={{ width: `${m.value ?? 0}%` }}
                />
              </div>
              <p className="mt-1.5 text-[13px] text-muted">{m.summary}</p>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
