import Link from 'next/link';

export function Logo({ href = '/' }: { href?: string }) {
  return (
    <Link href={href} className="flex items-center gap-2 text-ink" aria-label="ARWA home">
      <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden>
        <circle cx="16" cy="16" r="13" fill="none" stroke="var(--color-line-strong)" strokeWidth="3.5" />
        <path d="M16 3a13 13 0 0 1 12.4 9.1" fill="none" stroke="var(--color-ink)" strokeWidth="3.5" strokeLinecap="round" />
        <circle cx="16" cy="16" r="3.2" fill="var(--color-ink)" />
      </svg>
      <span className="text-[15px] font-semibold tracking-[0.2em]">ARWA</span>
    </Link>
  );
}
