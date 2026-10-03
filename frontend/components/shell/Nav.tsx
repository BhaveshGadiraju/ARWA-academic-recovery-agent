'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { Profile } from '@/lib/types';
import { Icon, type IconName } from '@/components/ui/Icon';
import { Logo } from '@/components/ui/Logo';
import { ProfileMenu } from './ProfileMenu';

const NAV: { href: string; label: string; icon: IconName }[] = [
  { href: '/dashboard', label: 'Home', icon: 'home' },
  { href: '/plan', label: 'Plan', icon: 'plan' },
  { href: '/courses', label: 'Courses', icon: 'courses' },
  { href: '/progress', label: 'Progress', icon: 'progress' },
  { href: '/arwa', label: 'ARWA', icon: 'spark' },
];

function useIsActive() {
  const pathname = usePathname();
  return (href: string) => pathname === href || pathname.startsWith(`${href}/`);
}

export function TopNav({ profile }: { profile: Profile }) {
  const isActive = useIsActive();
  return (
    <header className="sticky top-0 z-30 border-b border-line/70 bg-canvas/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Logo href="/dashboard" />
        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(item.href) ? 'page' : undefined}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                isActive(item.href) ? 'bg-ink text-surface' : 'text-muted hover:bg-sunken hover:text-ink'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <ProfileMenu profile={profile} />
      </div>
    </header>
  );
}

export function BottomNav() {
  const isActive = useIsActive();
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md md:hidden"
    >
      <div className="mx-auto grid max-w-md grid-cols-5">
        {NAV.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? 'page' : undefined}
              className={`flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium ${active ? 'text-ink' : 'text-faint'}`}
            >
              <Icon name={item.icon} size={22} />
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
