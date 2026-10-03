'use client';

import { useEffect, useMemo, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { ProfileContext } from '@/contexts/ProfileContext';
import { useApiData } from '@/hooks/useApi';
import type { Profile } from '@/lib/types';
import { ErrorState, LoadingState } from '@/components/ui/States';
import { BottomNav, TopNav } from './Nav';

/** Loads the profile, sends new students to onboarding, and renders the navigation chrome. */
export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: profile, error, reload } = useApiData<Profile>('/profile');

  useEffect(() => {
    if (profile && !profile.onboarding_completed) router.replace('/onboarding');
  }, [profile, router]);

  const context = useMemo(
    () => (profile ? { profile, refreshProfile: () => reload(true) } : null),
    [profile, reload],
  );

  if (error) return <ErrorState message={error} onRetry={() => reload()} />;
  if (!context || !context.profile.onboarding_completed) return <LoadingState label="Loading" />;

  return (
    <ProfileContext.Provider value={context}>
      <TopNav profile={context.profile} />
      <main className="mx-auto w-full max-w-6xl px-4 pb-28 pt-6 sm:px-6 md:pb-16 md:pt-8">{children}</main>
      <BottomNav />
    </ProfileContext.Provider>
  );
}
