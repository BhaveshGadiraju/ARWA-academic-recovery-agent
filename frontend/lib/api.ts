const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

/** An API failure with a message that is safe to show to students. */
export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

const FRIENDLY_STATUS: Record<number, string> = {
  401: 'Your session expired. Please log in again.',
  403: "You don't have access to that.",
  404: "We couldn't find that. It may have been deleted.",
  429: "You're going a little fast. Try again in a minute.",
  500: 'Something went wrong on our side. Please try again.',
  503: 'ARWA is temporarily unavailable. Please try again shortly.',
};

type ValidationIssue = { loc?: (string | number)[]; msg?: string };

function describeValidation(issues: ValidationIssue[]): string {
  const first = issues[0];
  if (!first) return 'Please check the form and try again.';
  const field = first.loc?.filter((part) => part !== 'body').join(' ');
  const message = (first.msg || 'Invalid value').replace(/^Value error, /, '');
  return field ? `${field.replace(/_/g, ' ')}: ${message}` : message;
}

async function toApiError(response: Response): Promise<ApiError> {
  let detail: unknown;
  try {
    detail = (await response.json()).detail;
  } catch {
    detail = undefined;
  }
  if (response.status === 422 && Array.isArray(detail)) {
    return new ApiError(describeValidation(detail), 422);
  }
  if (typeof detail === 'string' && response.status < 500) {
    return new ApiError(detail, response.status);
  }
  return new ApiError(FRIENDLY_STATUS[response.status] || FRIENDLY_STATUS[500], response.status);
}

export class ApiClient {
  /** Call the ARWA API. Throws ApiError with a user-friendly message on failure. */
  static async request<T = unknown>(method: HttpMethod, endpoint: string, data?: unknown, token?: string): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;

    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers,
        body: data === undefined ? undefined : JSON.stringify(data),
      });
    } catch {
      throw new ApiError("Can't reach ARWA right now. Check your connection and try again.", 0);
    }

    if (!response.ok) throw await toApiError(response);
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }
}
