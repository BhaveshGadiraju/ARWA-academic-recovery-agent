import type { ReactNode } from 'react';

/** Render **bold** and *italic* spans. Builds React nodes, never raw HTML. */
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) return <em key={i}>{part.slice(1, -1)}</em>;
    return part;
  });
}

/** Minimal formatting for ARWA replies: paragraphs, "- " bullet lists, bold, and italics. */
export function MessageText({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  let list: string[] = [];

  const flushList = () => {
    if (!list.length) return;
    blocks.push(
      <ul key={`ul-${blocks.length}`} className="list-disc space-y-1 pl-5">
        {list.map((item, i) => <li key={i}>{inline(item)}</li>)}
      </ul>,
    );
    list = [];
  };

  for (const raw of text.split('\n')) {
    const line = raw.trim();
    const bullet = line.match(/^[-*•]\s+(.*)$/) ?? line.match(/^\d+[.)]\s+(.*)$/);
    if (bullet) {
      list.push(bullet[1]);
      continue;
    }
    flushList();
    if (line) blocks.push(<p key={`p-${blocks.length}`}>{inline(line.replace(/^#+\s*/, ''))}</p>);
  }
  flushList();

  return <div className="space-y-2.5">{blocks}</div>;
}
