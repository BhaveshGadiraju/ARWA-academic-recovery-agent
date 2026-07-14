// API Request/Response Types

export interface AnalyzeRequest {
  name: string;
  major: string;
  current_gpa: number;
  target_gpa: number;
  courses: string[];
  study_hours_per_week: number;
  stress_level: number;
  goals: string;
}

export interface RecoverySuggestion {
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

export interface StudySession {
  day: string;
  time: string;
  duration: number;
  subject: string;
  activity: string;
}

export interface Resource {
  title: string;
  type: string;
  url?: string;
  description: string;
}

export interface AnalyzeResponse {
  summary: string;
  risk_assessment: {
    overall_risk_level: 'low' | 'medium' | 'high';
    risk_score: number;
    key_risks: string[];
  };
  strengths: string[];
  weaknesses: string[];
  recovery_plan: RecoverySuggestion[];
  study_schedule: StudySession[];
  mental_wellness_suggestions: string[];
  recommended_resources: Resource[];
  confidence_score: number;
  next_steps: string[];
}

// Student Profile
export interface StudentProfile {
  id: string;
  name: string;
  major: string;
  currentGpa: number;
  targetGpa: number;
  createdAt: Date;
  updatedAt: Date;
}

// Analysis History
export interface AnalysisHistory {
  id: string;
  studentId: string;
  studentName: string;
  analysisDate: Date;
  major: string;
  currentGpa: number;
  targetGpa: number;
  riskLevel: 'low' | 'medium' | 'high';
  confidenceScore: number;
  response: AnalyzeResponse;
}

// API Error
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

// Auth
export interface AuthState {
  isAuthenticated: boolean;
  user?: {
    id: string;
    email: string;
    name?: string;
  };
  loading: boolean;
  error?: string;
}
