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
      if ((error as any).message && (error as any).code) {
        // Already an ApiError-like object
        throw error as ApiError;
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

  /**
   * Transform the frontend AnalyzeRequest into the backend StudentRequest
   * then adapt the backend response into the AnalyzeResponse shape used
   * by the UI. This preserves the frontend form and types while wiring
   * it to the existing FastAPI backend.
   */
  async analyze(data: AnalyzeRequest): Promise<AnalyzeResponse> {
    // Build backend payload (StudentRequest)
    const backendPayload = {
      current_grade: data.current_gpa,
      stress_level: data.stress_level,
      available_time: data.study_hours_per_week,
      // Create minimal assignment entries from courses so backend scoring can run
      assignments: (data.courses || []).slice(0, 6).map((course: string) => ({
        title: `Work for ${course}`,
        course,
        difficulty: 0.5,
        estimated_hours: 3,
        days_remaining: 7,
        completed: false,
      })),
    };

    // Call backend
    const raw = await this.request<any>('/analyze', {
      method: 'POST',
      body: JSON.stringify(backendPayload),
    });

    // Map backend response to frontend AnalyzeResponse
    // Backend returns a rich object; key pieces are under `report` and `recovery_score`
    const report = raw.report || {};
    const recovery = raw.recovery_score || { after: { score: 0, status: 'Critical', probability: 0 } };

    const status = (recovery.after && recovery.after.status) || 'Critical';

    const mapStatusToRisk = (s: string) => {
      if (s === 'Excellent' || s === 'Good') return 'low';
      if (s === 'Recovering') return 'medium';
      return 'high';
    };

    const keyInsights: string[] = report.top_insights || [];
    const recommendedActions: string[] = report.recommended_actions || [];

    // Convert recommended actions into RecoverySuggestion objects
    const recovery_plan = (recommendedActions || []).map((act: string) => ({
      title: act,
      description: '',
      priority: /immediate|prioritize|urgent/i.test(act) ? 'high' : 'medium',
    }));

    const analyzeResponse: AnalyzeResponse = {
      summary: report.executive_summary || report.summary || (raw.forecast && String(raw.forecast)) || 'No summary available.',
      risk_assessment: {
        overall_risk_level: mapStatusToRisk(status),
        risk_score: (recovery.after && recovery.after.score) || 0,
        key_risks: keyInsights.slice(0, 5),
      },
      strengths: keyInsights,
      weaknesses: ((raw.academic_prediction && raw.academic_prediction.top_factors) || []).map((f: any) => `${f.factor}: ${f.contribution}%`) || [],
      recovery_plan,
      study_schedule: (raw.plan && raw.plan.schedule) || [],
      mental_wellness_suggestions: (recommendedActions || []).filter((a: string) => /burnout|rest|break|wellness|reduce/i.test(a)),
      recommended_resources: [],
      confidence_score: (report.confidence !== undefined) ? report.confidence : 0,
      next_steps: recommendedActions || [],
    };

    return analyzeResponse;
  }
}

export const apiClient = new ApiClient();

export type { AnalyzeRequest, AnalyzeResponse, ApiError };
