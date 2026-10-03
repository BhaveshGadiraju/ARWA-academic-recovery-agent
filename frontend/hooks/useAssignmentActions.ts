'use client';

import { useCallback } from 'react';
import type { Assignment } from '@/lib/types';
import { useApi } from './useApi';

/** Mutations shared by the checklist, plan, course page, and focus timer. */
export function useAssignmentActions() {
  const request = useApi();

  const setCompleted = useCallback(
    (id: string, completed: boolean) => request<Assignment>('PUT', `/assignments/${id}`, { completed }),
    [request],
  );

  const logStudy = useCallback(
    (assignmentId: string, minutes: number) =>
      request('POST', '/study-sessions', { assignment_id: assignmentId, minutes: Math.max(1, Math.round(minutes)) }),
    [request],
  );

  const remove = useCallback((id: string) => request<void>('DELETE', `/assignments/${id}`), [request]);

  return { setCompleted, logStudy, remove };
}
