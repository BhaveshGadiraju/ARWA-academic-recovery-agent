import type { ChatMessage } from '@/lib/types';
import { MessageText } from './MessageText';

export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-3xl rounded-br-lg bg-ink px-4 py-2.5 text-[15px] text-surface">
          {message.content}
        </p>
      </div>
    );
  }
  const tools = message.metadata?.tools_used ?? [];
  return (
    <div className="max-w-[92%] animate-fade-up">
      <div className="rounded-3xl rounded-bl-lg border border-line bg-surface px-4 py-3 text-[15px] leading-relaxed text-ink">
        <MessageText text={message.content} />
      </div>
      {(tools.length > 0 || message.metadata?.ai_powered === false) && (
        <p className="mt-1.5 px-2 text-[11px] text-faint">
          {tools.length > 0 && `Checked: ${tools.join(', ')}`}
          {message.metadata?.ai_powered === false && ' · answered from your plan (AI unavailable)'}
        </p>
      )}
    </div>
  );
}
