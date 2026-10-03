'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import type { Profile } from '@/lib/types';
import { Icon } from '@/components/ui/Icon';

function initials(profile: Profile): string {
  const source = profile.full_name || profile.email || '?';
  return source
    .split(/[\s@]+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('');
}

export function ProfileMenu({ profile }: { profile: Profile }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { signOut } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => ref.current && !ref.current.contains(e.target as Node) && setOpen(false);
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [open]);

  const logout = async () => {
    await signOut();
    router.replace('/');
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Account menu"
        aria-expanded={open}
        className="flex h-9 w-9 items-center justify-center rounded-full border border-line-strong bg-surface text-[13px] font-semibold text-ink hover:bg-sunken"
      >
        {initials(profile)}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-60 animate-fade-up rounded-2xl border border-line bg-surface p-2 shadow-lift">
          <div className="px-3 py-2">
            <p className="truncate text-sm font-medium">{profile.full_name || 'Student'}</p>
            <p className="truncate text-xs text-muted">{profile.email}</p>
          </div>
          <div className="my-1 h-px bg-line" />
          <Link
            href="/settings"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-ink-soft hover:bg-sunken"
          >
            <Icon name="settings" size={17} /> Settings
          </Link>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-ink-soft hover:bg-sunken"
          >
            <Icon name="logout" size={17} /> Log out
          </button>
        </div>
      )}
    </div>
  );
}
