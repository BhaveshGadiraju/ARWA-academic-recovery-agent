'use client';

import { useState, useCallback } from 'react';
import { apiClient, type AnalyzeRequest, type AnalyzeResponse, type ApiError } from '@/lib/api';

interface UseAnalysisState {
  loading: boolean;
  error: ApiError | null;
  data: AnalyzeResponse | null;
}

export function useAnalysis() {
  const [state, setState] = useState<UseAnalysisState>({
    loading: false,
    error: null,
    data: null,
  });

  const analyze = useCallback(async (request: AnalyzeRequest) => {
    setState({ loading: true, error: null, data: null });

    try {
      const response = await apiClient.analyze(request);
      setState({ loading: false, error: null, data: response });
      return response;
    } catch (error) {
      const apiError: ApiError = {
        message: error instanceof Error ? error.message : 'Analysis failed',
        code: (error as ApiError).code,
        details: (error as ApiError).details,
      };

      setState({ loading: false, error: apiError, data: null });
      throw apiError;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ loading: false, error: null, data: null });
  }, []);

  return {
    ...state,
    analyze,
    reset,
  };
}
