'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type { AuthState } from '@/lib/types';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    loading: false,
  });

  const login = useCallback(async (email: string, password: string) => {
    setAuthState(prev => ({ ...prev, loading: true, error: undefined }));
    try {
      // TODO: Implement Supabase login
      // For now, this is a placeholder
      setAuthState({
        isAuthenticated: true,
        user: { id: '1', email, name: email.split('@')[0] },
        loading: false,
      });
    } catch (error) {
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Login failed',
      }));
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    setAuthState(prev => ({ ...prev, loading: true }));
    try {
      // TODO: Implement Supabase logout
      setAuthState({
        isAuthenticated: false,
        loading: false,
      });
    } catch (error) {
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Logout failed',
      }));
      throw error;
    }
  }, []);

  const signup = useCallback(async (email: string, password: string, name: string) => {
    setAuthState(prev => ({ ...prev, loading: true, error: undefined }));
    try {
      // TODO: Implement Supabase signup
      setAuthState({
        isAuthenticated: true,
        user: { id: '1', email, name },
        loading: false,
      });
    } catch (error) {
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Signup failed',
      }));
      throw error;
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        logout,
        signup,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
