'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiClient, ApiError, HttpMethod } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

/** Returns a request function that attaches the current session token. */
export function useApi() {
  const { session, signOut } = useAuth();
  const token = session?.access_token;

  return useCallback(
    async <T>(method: HttpMethod, path: string, body?: unknown): Promise<T> => {
      try {
        return await ApiClient.request<T>(method, path, body, token);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) await signOut();
        throw err;
      }
    },
    [token, signOut],
  );
}

interface ApiData<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  /** Re-fetch. Pass `true` to keep showing current data while refreshing. */
  reload: (silent?: boolean) => Promise<void>;
  setData: (value: T | null) => void;
}

/** Load a GET endpoint for the signed-in user. Pass null to skip loading. */
export function useApiData<T>(path: string | null): ApiData<T> {
  const request = useApi();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(path));
  const latest = useRef(0);

  const reload = useCallback(
    async (silent = false) => {
      if (!path) return;
      const call = ++latest.current;
      if (!silent) setLoading(true);
      setError(null);
      try {
        const result = await request<T>('GET', path);
        if (call === latest.current) setData(result);
      } catch (err) {
        if (call === latest.current) setError(err instanceof Error ? err.message : 'Something went wrong.');
      } finally {
        if (call === latest.current) setLoading(false);
      }
    },
    [path, request],
  );

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, error, loading, reload, setData };
}
