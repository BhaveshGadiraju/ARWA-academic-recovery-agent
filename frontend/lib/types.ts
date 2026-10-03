// Mirrors the backend response models (models/schemas.py and models/insights.py).

export type Severity = 'critical' | 'high' | 'moderate' | 'low';
export type Category = 'homework' | 'exam' | 'quiz' | 'project' | 'lab' | 'reading' | 'paper' | 'other';
export type CourseStatus = 'on_track' | 'watch' | 'at_risk' | 'no_data';
export type ScoreBand = 'on_track' | 'manageable' | 'under_pressure' | 'needs_recovery' | 'not_enough_data';

export interface Profile {
  id: string;
  email: string | null;
  full_name: string | null;
  school: string | null;
  major: string | null;
  year_in_school: string | null;
  timezone: string;
  onboarding_completed: boolean;
}

export interface AvailabilityDay {
  weekday: number;
  minutes: number;
  start_time: string;
}

export interface Semester {
  id: string;
  name: string;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
}

export interface Course {
  id: string;
  semester_id: string;
  name: string;
  code: string | null;
  credits: number;
  target_grade: number | null;
}

export interface Assignment {
  id: string;
  title: string;
  course: string | null;
  course_id: string | null;
  course_code: string | null;
  category: Category;
  difficulty: number;
  estimated_hours: number;
  due_date: string;
  completed: boolean;
  completed_at: string | null;
  points_possible: number | null;
  points_earned: number | null;
  notes: string | null;
}

export interface AssignmentInput {
  title: string;
  course_id: string;
  category: Category;
  estimated_hours: number;
  due_date: string;
  completed?: boolean;
  points_possible?: number | null;
  points_earned?: number | null;
  notes?: string | null;
}

export interface ScoreFactor {
  key: string;
  label: string;
  detail: string;
  impact: 'positive' | 'negative' | 'neutral';
  value: number | null;
  weight: number;
  points_lost: number;
}

export interface RecoveryScore {
  score: number | null;
  band: ScoreBand;
  band_label: string;
  headline: string;
  factors: ScoreFactor[];
  previous_score: number | null;
  delta: number | null;
}

export interface Metric {
  key: 'workload' | 'deadline_pressure' | 'performance' | 'capacity';
  label: string;
  value: number | null;
  level: string;
  summary: string;
  meaning: string;
  higher_is_better: boolean;
}

export interface Risk {
  id: string;
  severity: Severity;
  kind: string;
  title: string;
  reason: string;
  action: string;
  course_id: string | null;
  course_name: string | null;
  assignment_id: string | null;
  data: Record<string, unknown>;
}

export interface PriorityItem {
  rank: number;
  assignment_id: string;
  title: string;
  course_id: string | null;
  course_name: string | null;
  category: Category;
  due_date: string;
  days_until_due: number;
  remaining_minutes: number;
  reason: string;
}

export interface PlanBlock {
  kind: 'study' | 'break';
  start: string;
  end: string;
  minutes: number;
  assignment_id?: string | null;
  title?: string | null;
  course_name?: string | null;
  category?: Category | null;
  due_date?: string | null;
}

export interface PlanDay {
  date: string;
  label: string;
  window_minutes: number;
  study_minutes: number;
  blocks: PlanBlock[];
}

export interface UnscheduledWork {
  assignment_id: string;
  title: string;
  course_name: string | null;
  due_date: string;
  unscheduled_minutes: number;
}

export interface RecoveryPlan {
  generated_at: string;
  days: PlanDay[];
  unscheduled: UnscheduledWork[];
  required_minutes: number;
  planned_minutes: number;
  is_feasible: boolean;
}

export interface CourseHealth {
  course_id: string;
  name: string;
  code: string | null;
  credits: number;
  grade: number | null;
  target_grade: number | null;
  health: number | null;
  status: CourseStatus;
  summary: string;
  trend: number | null;
  pending_count: number;
  pending_minutes: number;
  completion_rate: number | null;
  next_due: { assignment_id: string; title: string; category: Category; due_date: string; days_until_due: number } | null;
}

export interface Dashboard {
  generated_at: string;
  setup: {
    onboarding_completed: boolean;
    has_courses: boolean;
    has_assignments: boolean;
    has_availability: boolean;
    has_grades: boolean;
  };
  score: RecoveryScore;
  metrics: Metric[];
  today: {
    academic_load: string;
    deadline_pressure: string;
    available_minutes_today: number;
    tasks_remaining: number;
    overdue_count: number;
  };
  risks: Risk[];
  priorities: PriorityItem[];
  plan_today: PlanDay | null;
  insight: { message: string; action_label: string | null; action_assignment_id: string | null };
  courses: CourseHealth[];
  trend: TrendPoint[];
}

export interface TrendPoint {
  date: string;
  score: number;
}

export interface CourseDetail {
  course: Course;
  health: CourseHealth;
  assignments: Assignment[];
  risks: Risk[];
  recommended_action: string;
}

export interface Progress {
  score_history: TrendPoint[];
  study_days: { date: string; studied_minutes: number; planned_minutes: number | null }[];
  weekly_completion: { week_start: string; completed: number; on_time: number }[];
  missed: { assignment_id: string; title: string; course_name: string | null; due_date: string; status: 'overdue' | 'late' }[];
  course_trends: { course_id: string; name: string; points: { date: string; grade: number; title: string }[] }[];
  totals: Record<string, number>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  metadata: { tools_used?: string[]; ai_powered?: boolean };
  created_at: string;
}

export interface ChatReply {
  message: ChatMessage;
  tools_used: string[];
  ai_powered: boolean;
}

export interface Wellness {
  id: string;
  stress_level: number;
  sleep_hours: number | null;
  energy_level: number | null;
  note: string | null;
  created_at: string;
}
