-- ============================================================================
-- ARWA Initial Schema Migration
-- Created: 2026-08-10
-- Tables: profiles, assignments, analyses, analysis_assignments,
--         risk_factors, priorities, recommendations,
--         recovery_plan_days, recovery_plan_tasks, explanations
-- ============================================================================

-- ============================================================================
-- 1. PROFILES
-- Extends auth.users with optional profile data.
-- Created automatically on signup via trigger.
-- ============================================================================

CREATE TABLE profiles (
  id         uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name  text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "profiles_insert_own" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "profiles_update_own" ON profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "profiles_delete_own" ON profiles
  FOR DELETE USING (auth.uid() = id);

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data ->> 'full_name', NULL)
  );
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Auto-update updated_at on profile changes
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 2. ASSIGNMENTS
-- Persistent assignments owned by a user. Survives across analyses.
-- ============================================================================

CREATE TABLE assignments (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title           text NOT NULL,
  course          text NOT NULL,
  difficulty      float NOT NULL DEFAULT 0.5
                  CHECK (difficulty >= 0 AND difficulty <= 1),
  estimated_hours float NOT NULL
                  CHECK (estimated_hours >= 0),
  due_date        date NOT NULL,
  completed       boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "assignments_select_own" ON assignments
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "assignments_insert_own" ON assignments
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "assignments_update_own" ON assignments
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "assignments_delete_own" ON assignments
  FOR DELETE USING (auth.uid() = user_id);

CREATE INDEX idx_assignments_user_id ON assignments (user_id);
CREATE INDEX idx_assignments_due_date ON assignments (due_date);
CREATE INDEX idx_assignments_user_due ON assignments (user_id, due_date);

CREATE TRIGGER assignments_updated_at
  BEFORE UPDATE ON assignments
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 3. ANALYSES
-- One record per analysis run. Contains input values and top-level results.
-- ============================================================================

CREATE TABLE analyses (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Input
  current_grade  float NOT NULL CHECK (current_grade >= 0 AND current_grade <= 100),
  stress_level   float NOT NULL CHECK (stress_level >= 1 AND stress_level <= 10),
  available_time float NOT NULL CHECK (available_time >= 0),

  -- Meta
  ai_powered     boolean NOT NULL DEFAULT false,
  fallback_used  boolean NOT NULL DEFAULT false,

  -- Academic Risk
  academic_risk_score        int NOT NULL CHECK (academic_risk_score >= 0 AND academic_risk_score <= 100),
  academic_risk_level        text NOT NULL CHECK (academic_risk_level IN ('LOW','MODERATE','HIGH','CRITICAL')),
  academic_risk_explanation  text NOT NULL,

  -- Burnout Risk
  burnout_risk_score        int NOT NULL CHECK (burnout_risk_score >= 0 AND burnout_risk_score <= 100),
  burnout_risk_level        text NOT NULL CHECK (burnout_risk_level IN ('LOW','MODERATE','HIGH','CRITICAL')),
  burnout_risk_explanation  text NOT NULL,

  -- Recovery Score
  recovery_score_value       int NOT NULL CHECK (recovery_score_value >= 0 AND recovery_score_value <= 100),
  recovery_score_explanation text NOT NULL,

  -- Summary
  overall_summary text NOT NULL,

  -- Timestamps
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "analyses_select_own" ON analyses
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "analyses_insert_own" ON analyses
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "analyses_update_own" ON analyses
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "analyses_delete_own" ON analyses
  FOR DELETE USING (auth.uid() = user_id);

CREATE INDEX idx_analyses_user_id ON analyses (user_id);
CREATE INDEX idx_analyses_created_at ON analyses (created_at DESC);
CREATE INDEX idx_analyses_user_created ON analyses (user_id, created_at DESC);


-- ============================================================================
-- 4. ANALYSIS_ASSIGNMENTS
-- Immutable snapshot of assignment data at the time of analysis.
-- ============================================================================

CREATE TABLE analysis_assignments (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id     uuid NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  title           text NOT NULL,
  course          text NOT NULL,
  difficulty      float NOT NULL CHECK (difficulty >= 0 AND difficulty <= 1),
  estimated_hours float NOT NULL CHECK (estimated_hours >= 0),
  days_remaining  int NOT NULL CHECK (days_remaining >= 0),
  completed       boolean NOT NULL
);

ALTER TABLE analysis_assignments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "analysis_assignments_select_own" ON analysis_assignments
  FOR SELECT USING (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE POLICY "analysis_assignments_insert_own" ON analysis_assignments
  FOR INSERT WITH CHECK (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE INDEX idx_analysis_assignments_analysis_id ON analysis_assignments (analysis_id);


-- ============================================================================
-- 5. RISK_FACTORS
-- Normalized risk factor rows per analysis.
-- ============================================================================

CREATE TABLE risk_factors (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id uuid NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  factor      text NOT NULL,
  severity    text NOT NULL CHECK (severity IN ('LOW','MODERATE','HIGH','CRITICAL')),
  impact      int NOT NULL CHECK (impact >= 0 AND impact <= 100),
  evidence    text NOT NULL,
  explanation text NOT NULL
);

ALTER TABLE risk_factors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "risk_factors_select_own" ON risk_factors
  FOR SELECT USING (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE POLICY "risk_factors_insert_own" ON risk_factors
  FOR INSERT WITH CHECK (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE INDEX idx_risk_factors_analysis_id ON risk_factors (analysis_id);


-- ============================================================================
-- 6. PRIORITIES
-- Normalized priority rows per analysis.
-- ============================================================================

CREATE TABLE priorities (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id    uuid NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  rank           int NOT NULL CHECK (rank >= 1),
  course_or_task text NOT NULL,
  priority       text NOT NULL CHECK (priority IN ('LOW','MODERATE','HIGH','CRITICAL')),
  reason         text NOT NULL
);

ALTER TABLE priorities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "priorities_select_own" ON priorities
  FOR SELECT USING (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE POLICY "priorities_insert_own" ON priorities
  FOR INSERT WITH CHECK (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE INDEX idx_priorities_analysis_id ON priorities (analysis_id);


-- ============================================================================
-- 7. RECOMMENDATIONS
-- Normalized recommendation rows per analysis.
-- ============================================================================

CREATE TABLE recommendations (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id      uuid NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  action           text NOT NULL,
  reason           text NOT NULL,
  priority         text NOT NULL CHECK (priority IN ('LOW','MODERATE','HIGH','CRITICAL')),
  expected_impact  text NOT NULL
);

ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "recommendations_select_own" ON recommendations
  FOR SELECT USING (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE POLICY "recommendations_insert_own" ON recommendations
  FOR INSERT WITH CHECK (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE INDEX idx_recommendations_analysis_id ON recommendations (analysis_id);


-- ============================================================================
-- 8. RECOVERY_PLAN_DAYS
-- Each day in the recovery plan.
-- ============================================================================

CREATE TABLE recovery_plan_days (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id           uuid NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  date                  date NOT NULL,
  total_study_minutes   int NOT NULL CHECK (total_study_minutes >= 0)
);

ALTER TABLE recovery_plan_days ENABLE ROW LEVEL SECURITY;

CREATE POLICY "recovery_plan_days_select_own" ON recovery_plan_days
  FOR SELECT USING (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE POLICY "recovery_plan_days_insert_own" ON recovery_plan_days
  FOR INSERT WITH CHECK (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE INDEX idx_recovery_plan_days_analysis_id ON recovery_plan_days (analysis_id);


-- ============================================================================
-- 9. RECOVERY_PLAN_TASKS
-- Tasks within each plan day.
-- ============================================================================

CREATE TABLE recovery_plan_tasks (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_day_id      uuid NOT NULL REFERENCES recovery_plan_days(id) ON DELETE CASCADE,
  course           text NOT NULL,
  task             text NOT NULL,
  duration_minutes int NOT NULL CHECK (duration_minutes >= 0),
  priority         text NOT NULL CHECK (priority IN ('LOW','MODERATE','HIGH','CRITICAL')),
  reason           text NOT NULL
);

ALTER TABLE recovery_plan_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "recovery_plan_tasks_select_own" ON recovery_plan_tasks
  FOR SELECT USING (
    plan_day_id IN (
      SELECT rpd.id FROM recovery_plan_days rpd
      JOIN analyses a ON rpd.analysis_id = a.id
      WHERE a.user_id = auth.uid()
    )
  );

CREATE POLICY "recovery_plan_tasks_insert_own" ON recovery_plan_tasks
  FOR INSERT WITH CHECK (
    plan_day_id IN (
      SELECT rpd.id FROM recovery_plan_days rpd
      JOIN analyses a ON rpd.analysis_id = a.id
      WHERE a.user_id = auth.uid()
    )
  );

CREATE INDEX idx_recovery_plan_tasks_plan_day_id ON recovery_plan_tasks (plan_day_id);


-- ============================================================================
-- 10. EXPLANATIONS
-- Normalized explanation rows per analysis.
-- ============================================================================

CREATE TABLE explanations (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id       uuid NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  recommendation    text NOT NULL,
  detected_signal   text NOT NULL,
  why_it_matters    text NOT NULL,
  why_this_action   text NOT NULL,
  expected_result   text NOT NULL
);

ALTER TABLE explanations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "explanations_select_own" ON explanations
  FOR SELECT USING (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE POLICY "explanations_insert_own" ON explanations
  FOR INSERT WITH CHECK (
    analysis_id IN (SELECT id FROM analyses WHERE user_id = auth.uid())
  );

CREATE INDEX idx_explanations_analysis_id ON explanations (analysis_id);
