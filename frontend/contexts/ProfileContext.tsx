'use client';

import { createContext, useContext } from 'react';
import type { Profile } from '@/lib/types';

interface ProfileContextType {
  profile: Profile;
  refreshProfile: () => Promise<void>;
}

export const ProfileContext = createContext<ProfileContextType | null>(null);

/** The signed-in student's profile. Only available inside the app shell. */
export function useProfile(): ProfileContextType {
  const value = useContext(ProfileContext);
  if (!value) throw new Error('useProfile must be used inside the app shell');
  return value;
}
