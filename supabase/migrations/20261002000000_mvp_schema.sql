-- ============================================================================
-- ARWA MVP Schema
-- Created: 2026-10-02
--
-- Extends the initial schema with the structured academic data the MVP needs:
--   profiles (extended), semesters, courses, assignments (extended),
--   study_availability, wellness_checkins, study_sessions,
--   recovery_snapshots, chat_messages
--
-- Every table is owned by a user and protected by RLS. Child rows that point
-- at another row (course -> semester, assignment -> course, session ->
-- assignment) are only insertable/updatable when the parent belongs to the
-- same user, so a client cannot attach data to someone else's records.
-- ============================================================================


ALTER FUNCTION update_updated_at() SET search_path = '';


-- ============================================================================
-- 1. PROFILES — academic profile + onboarding state
-- ============================================================================

ALTER TABLE profiles
  ADD COLUMN school               text CHECK (char_length(school) <= 120),
  ADD COLUMN major                text CHECK (char_length(major) <= 120),
  ADD COLUMN year_in_school       text CHECK (char_length(year_in_school) <= 40),
  ADD COLUMN timezone             text NOT NULL DEFAULT 'America/New_York'
                                  CHECK (char_length(timezone) <= 64),
  ADD COLUMN onboarding_completed boolean NOT NULL DEFAULT false;

ALTER TABLE profiles
  ADD CONSTRAINT profiles_full_name_len CHECK (char_length(full_name) <= 120);


-- ============================================================================
-- 2. SEMESTERS
-- ============================================================================

CREATE TABLE semesters (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  name        text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 80),
  start_date  date,
  end_date    date,
  is_current  boolean NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  CHECK (start_date IS NULL OR end_date IS NULL OR end_date >= start_date)
);

CREATE UNIQUE INDEX semesters_one_current_per_user ON semesters (user_id) WHERE is_current;
CREATE INDEX idx_semesters_user_id ON semesters (user_id);

ALTER TABLE semesters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "semesters_select_own" ON semesters
  FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "semesters_insert_own" ON semesters
  FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "semesters_update_own" ON semesters
  FOR UPDATE TO authenticated
  USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "semesters_delete_own" ON semesters
  FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

CREATE TRIGGER semesters_updated_at
  BEFORE UPDATE ON semesters
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 3. COURSES
-- ============================================================================

CREATE TABLE courses (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  semester_id   uuid NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
  name          text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 120),
  code          text CHECK (char_length(code) <= 30),
  credits       numeric(3,1) NOT NULL DEFAULT 3 CHECK (credits > 0 AND credits <= 12),
  target_grade  numeric(5,2) CHECK (target_grade >= 0 AND target_grade <= 100),
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_courses_user_id ON courses (user_id);
CREATE INDEX idx_courses_semester_id ON courses (semester_id);

ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "courses_select_own" ON courses
  FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "courses_insert_own" ON courses
  FOR INSERT TO authenticated WITH CHECK (
    (SELECT auth.uid()) = user_id
    AND EXISTS (SELECT 1 FROM semesters s WHERE s.id = semester_id AND s.user_id = (SELECT auth.uid()))
  );
CREATE POLICY "courses_update_own" ON courses
  FOR UPDATE TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK (
    (SELECT auth.uid()) = user_id
    AND EXISTS (SELECT 1 FROM semesters s WHERE s.id = semester_id AND s.user_id = (SELECT auth.uid()))
  );
CREATE POLICY "courses_delete_own" ON courses
  FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

CREATE TRIGGER courses_updated_at
  BEFORE UPDATE ON courses
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 4. ASSIGNMENTS — link to courses, add grading + category fields
-- The legacy free-text `course` column is kept (nullable) so the existing
-- /assignments contract keeps working; new rows use course_id.
-- ============================================================================

ALTER TABLE assignments
  ADD COLUMN course_id        uuid REFERENCES courses(id) ON DELETE CASCADE,
  ADD COLUMN category         text NOT NULL DEFAULT 'homework'
                              CHECK (category IN ('homework','exam','quiz','project','lab','reading','paper','other')),
  ADD COLUMN points_possible  numeric(7,2) CHECK (points_possible > 0),
  ADD COLUMN points_earned    numeric(7,2) CHECK (points_earned >= 0),
  ADD COLUMN completed_at     timestamptz,
  ADD COLUMN notes            text CHECK (char_length(notes) <= 2000);

ALTER TABLE assignments ALTER COLUMN course DROP NOT NULL;

ALTER TABLE assignments
  ADD CONSTRAINT assignments_title_len CHECK (char_length(title) BETWEEN 1 AND 200),
  ADD CONSTRAINT assignments_estimated_hours_max CHECK (estimated_hours <= 200),
  ADD CONSTRAINT assignments_earned_requires_possible
    CHECK (points_earned IS NULL OR points_possible IS NOT NULL),
  ADD CONSTRAINT assignments_earned_max
    CHECK (points_earned IS NULL OR points_earned <= points_possible * 1.5);

CREATE INDEX idx_assignments_course_id ON assignments (course_id);

DROP POLICY "assignments_select_own" ON assignments;
DROP POLICY "assignments_insert_own" ON assignments;
DROP POLICY "assignments_update_own" ON assignments;
DROP POLICY "assignments_delete_own" ON assignments;

CREATE POLICY "assignments_select_own" ON assignments
  FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "assignments_insert_own" ON assignments
  FOR INSERT TO authenticated WITH CHECK (
    (SELECT auth.uid()) = user_id
    AND (course_id IS NULL OR EXISTS (
      SELECT 1 FROM courses c WHERE c.id = course_id AND c.user_id = (SELECT auth.uid())
    ))
  );
CREATE POLICY "assignments_update_own" ON assignments
  FOR UPDATE TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK (
    (SELECT auth.uid()) = user_id
    AND (course_id IS NULL OR EXISTS (
      SELECT 1 FROM courses c WHERE c.id = course_id AND c.user_id = (SELECT auth.uid())
    ))
  );
CREATE POLICY "assignments_delete_own" ON assignments
  FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);


-- ============================================================================
-- 5. STUDY_AVAILABILITY — weekly study time, one row per weekday
-- weekday follows Python's date.weekday(): 0 = Monday ... 6 = Sunday
-- ============================================================================

CREATE TABLE study_availability (
  user_id     uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  weekday     smallint NOT NULL CHECK (weekday BETWEEN 0 AND 6),
  minutes     int NOT NULL CHECK (minutes BETWEEN 0 AND 960),
  start_time  time NOT NULL DEFAULT '18:00',
  PRIMARY KEY (user_id, weekday)
);

ALTER TABLE study_availability ENABLE ROW LEVEL SECURITY;

CREATE POLICY "study_availability_select_own" ON study_availability
  FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "study_availability_insert_own" ON study_availability
  FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "study_availability_update_own" ON study_availability
  FOR UPDATE TO authenticated
  USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "study_availability_delete_own" ON study_availability
  FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);


-- ============================================================================
-- 6. WELLNESS_CHECKINS — optional stress / sleep / energy inputs
-- ============================================================================

CREATE TABLE wellness_checkins (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  stress_level  smallint NOT NULL CHECK (stress_level BETWEEN 1 AND 10),
  sleep_hours   numeric(3,1) CHECK (sleep_hours >= 0 AND sleep_hours <= 24),
  energy_level  smallint CHECK (energy_level BETWEEN 1 AND 5),
  note          text CHECK (char_length(note) <= 500),
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_wellness_user_created ON wellness_checkins (user_id, created_at DESC);

ALTER TABLE wellness_checkins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "wellness_select_own" ON wellness_checkins
  FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "wellness_insert_own" ON wellness_checkins
  FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "wellness_delete_own" ON wellness_checkins
  FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);


-- ============================================================================
-- 7. STUDY_SESSIONS — logged work on an assignment (plan block completion)
-- ============================================================================

CREATE TABLE study_sessions (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  assignment_id  uuid NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
  minutes        int NOT NULL CHECK (minutes BETWEEN 1 AND 720),
  session_date   date NOT NULL DEFAULT current_date,
  created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_study_sessions_user_date ON study_sessions (user_id, session_date DESC);
CREATE INDEX idx_study_sessions_assignment ON study_sessions (assignment_id);

ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "study_sessions_select_own" ON study_sessions
  FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "study_sessions_insert_own" ON study_sessions
  FOR INSERT TO authenticated WITH CHECK (
    (SELECT auth.uid()) = user_id
    AND EXISTS (
      SELECT 1 FROM assignments a WHERE a.id = assignment_id AND a.user_id = (SELECT auth.uid())
    )
  );
CREATE POLICY "study_sessions_delete_own" ON study_sessions
  FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);


-- ============================================================================
-- 8. RECOVERY_SNAPSHOTS — one deterministic Recovery Score per user per day
-- ============================================================================

CREATE TABLE recovery_snapshots (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  snapshot_date  date NOT NULL,
  score          int NOT NULL CHECK (score BETWEEN 0 AND 100),
  metrics        jsonb NOT NULL DEFAULT '{}'::jsonb,
  factors        jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, snapshot_date)
);

ALTER TABLE recovery_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "recovery_snapshots_select_own" ON recovery_snapshots
  FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "recovery_snapshots_insert_own" ON recovery_snapshots
  FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "recovery_snapshots_update_own" ON recovery_snapshots
  FOR UPDATE TO authenticated
  USING ((SELECT auth.uid()) = user_id) WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE TRIGGER recovery_snapshots_updated_at
  BEFORE UPDATE ON recovery_snapshots
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 9. CHAT_MESSAGES — ARWA agent conversation history
-- ============================================================================

CREATE TABLE chat_messages (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  role        text NOT NULL CHECK (role IN ('user','assistant')),
  content     text NOT NULL CHECK (char_length(content) BETWEEN 1 AND 8000),
  metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_chat_messages_user_created ON chat_messages (user_id, created_at DESC);

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "chat_messages_select_own" ON chat_messages
  FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "chat_messages_insert_own" ON chat_messages
  FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "chat_messages_delete_own" ON chat_messages
  FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);


-- ============================================================================
-- 10. GRANTS — only signed-in users reach these tables through the Data API
-- ============================================================================

REVOKE ALL ON
  profiles, assignments, analyses, analysis_assignments, risk_factors, priorities,
  recommendations, recovery_plan_days, recovery_plan_tasks, explanations,
  semesters, courses, study_availability, wellness_checkins, study_sessions,
  recovery_snapshots, chat_messages
FROM anon;

GRANT SELECT, INSERT, UPDATE, DELETE ON
  profiles, assignments, analyses, analysis_assignments, risk_factors, priorities,
  recommendations, recovery_plan_days, recovery_plan_tasks, explanations,
  semesters, courses, study_availability, wellness_checkins, study_sessions,
  recovery_snapshots, chat_messages
TO authenticated;
