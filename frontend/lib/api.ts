import type { AnalyzeRequest, AnalyzeResponse, ApiError } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  console.warn('[API] NEXT_PUBLIC_API_URL is not set. API calls will fail.');
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error: ApiError = {
          message: `API Error: ${response.status} ${response.statusText}`,
          code: response.status.toString(),
        };

        try {
          const errorData = await response.json();
          error.details = errorData;
        } catch {
          // Response wasn't JSON, use default error
        }

        throw error;
      }

      const data = await response.json();
      return data as T;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof TypeError) {
        throw {
          message: 'Network error. Please check your connection.',
          code: 'NETWORK_ERROR',
        } as ApiError;
      }

      throw {
        message: 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR',
        details: error,
      } as ApiError;
    }
  }

  async analyze(data: AnalyzeRequest): Promise<AnalyzeResponse> {
    return this.request<AnalyzeResponse>('/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new ApiClient();

export type { AnalyzeRequest, AnalyzeResponse, ApiError };
