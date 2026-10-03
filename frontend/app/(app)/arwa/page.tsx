'use client';

import { Suspense, useEffect, useRef, useState, type FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import type { ChatMessage, ChatReply } from '@/lib/types';
import { useApi, useApiData } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { FormError } from '@/components/ui/Field';
import { Icon } from '@/components/ui/Icon';
import { ErrorState, LoadingState } from '@/components/ui/States';
import { ChatMessageBubble } from '@/components/arwa/ChatMessageBubble';

const SUGGESTIONS = [
  'What should I work on tonight?',
  'Why is my Recovery Score what it is?',
  'Can I realistically finish everything this week?',
  'Which course needs the most attention?',
];

export default function ArwaPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading" />}>
      <ArwaChat />
    </Suspense>
  );
}

function pendingMessage(content: string): ChatMessage {
  return { id: `pending-${Date.now()}`, role: 'user', content, metadata: {}, created_at: new Date().toISOString() };
}

function ArwaChat() {
  const request = useApi();
  const router = useRouter();
  const params = useSearchParams();
  const { data: history, error, loading, reload, setData } = useApiData<ChatMessage[]>('/chat/messages');
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const sentInitial = useRef(false);
  const messages = history ?? [];

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, thinking]);

  const send = async (text: string) => {
    const content = text.trim();
    if (!content || thinking) return;
    setSendError(null);
    setInput('');
    setThinking(true);
    const optimistic = [...messages, pendingMessage(content)];
    setData(optimistic);
    try {
      const reply = await request<ChatReply>('POST', '/chat', { message: content });
      setData([...optimistic, reply.message]);
    } catch (err) {
      setSendError(err instanceof Error ? err.message : 'ARWA could not answer right now.');
      setData(messages);
      setInput(content);
    } finally {
      setThinking(false);
    }
  };

  useEffect(() => {
    const q = params.get('q');
    if (q && history && !sentInitial.current) {
      sentInitial.current = true;
      router.replace('/arwa');
      send(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- send once, when history first loads
  }, [history]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    send(input);
  };

  const clear = async () => {
    if (!window.confirm('Clear this conversation?')) return;
    await request('DELETE', '/chat/messages');
    setData([]);
  };

  if (loading && !history) return <LoadingState label="Loading" />;
  if (error && !history) return <ErrorState message={error} onRetry={() => reload()} />;

  return (
    <div className="mx-auto flex max-w-2xl animate-fade-up flex-col">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-[26px] font-semibold tracking-tight">
            <Icon name="spark" size={22} /> ARWA
          </h1>
          <p className="text-sm text-muted">Answers come from your courses, deadlines, grades, and study time.</p>
        </div>
        {messages.length > 0 && (
          <Button variant="ghost" size="sm" onClick={clear}>Clear</Button>
        )}
      </div>

      <div className="min-h-[50vh] space-y-4 pb-4">
        {messages.length === 0 && !thinking && (
          <div className="rounded-3xl border border-line bg-surface p-6">
            <p className="text-[15px] font-medium">Ask me about your week.</p>
            <p className="mt-1 text-sm text-muted">I only use what you&apos;ve entered in ARWA, and I&apos;ll tell you when something is missing.</p>
            <div className="mt-5 flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} className="rounded-full border border-line-strong px-3.5 py-2 text-left text-[13px] text-ink-soft hover:bg-sunken">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => <ChatMessageBubble key={m.id} message={m} />)}
        {thinking && (
          <p className="animate-pulse-soft px-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
            ARWA is checking your data…
          </p>
        )}
        <div ref={bottom} />
      </div>

      <div className="sticky bottom-20 md:bottom-4">
        <FormError message={sendError} />
        <form onSubmit={submit} className="mt-2 flex items-end gap-2 rounded-3xl border border-line-strong bg-surface p-2 pl-4 shadow-lift">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            rows={1}
            maxLength={2000}
            placeholder="Ask ARWA…"
            aria-label="Message ARWA"
            className="max-h-40 min-h-[40px] flex-1 resize-none bg-transparent py-2 text-[15px] focus:outline-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || thinking}
            aria-label="Send"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-ink text-surface disabled:opacity-40"
          >
            <Icon name="arrowUp" size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
