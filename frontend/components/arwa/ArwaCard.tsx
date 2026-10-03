'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import type { Dashboard } from '@/lib/types';
import { Button, ButtonLink } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';

interface Props {
  insight: Dashboard['insight'];
  onStart: () => void;
}

/** ARWA's headline recommendation with one action and a quick "Ask ARWA" box. */
export function ArwaCard({ insight, onStart }: Props) {
  const router = useRouter();
  const [question, setQuestion] = useState('');

  const ask = (e: FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    router.push(q ? `/arwa?q=${encodeURIComponent(q)}` : '/arwa');
  };

  const action = (() => {
    if (!insight.action_label) return null;
    if (insight.action_label.startsWith('Start') && insight.action_assignment_id) {
      return <Button onClick={onStart} size="sm" className="!bg-surface !text-ink hover:!bg-canvas">{insight.action_label}</Button>;
    }
    const href = insight.action_label === 'Set study time' ? '/settings' : '/plan';
    return <ButtonLink href={href} size="sm" className="!bg-surface !text-ink hover:!bg-canvas">{insight.action_label}</ButtonLink>;
  })();

  return (
    <section className="rounded-3xl bg-ink p-5 text-surface shadow-lift sm:p-6">
      <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-surface/60">
        <Icon name="spark" size={15} /> ARWA
      </div>
      <p className="mt-3 text-[16px] leading-relaxed">{insight.message}</p>
      {action && <div className="mt-4">{action}</div>}
      <form onSubmit={ask} className="mt-5 flex items-center gap-2 rounded-full bg-surface/10 p-1.5 pl-4">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask ARWA anything about your week"
          aria-label="Ask ARWA"
          maxLength={2000}
          className="min-w-0 flex-1 bg-transparent text-sm text-surface placeholder:text-surface/50 focus:outline-none"
        />
        <button type="submit" aria-label="Send" className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface text-ink">
          <Icon name="arrowUp" size={16} />
        </button>
      </form>
    </section>
  );
}
