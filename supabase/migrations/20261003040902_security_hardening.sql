-- ============================================================================
-- Security and RLS performance hardening (Supabase advisor findings).
--
-- 1. handle_new_user() is a SECURITY DEFINER trigger function. It must only
--    run from the auth.users trigger, never through /rest/v1/rpc.
-- 2. Policies from the initial schema called auth.uid() once per row. Wrapping
--    it as (select auth.uid()) evaluates it once per query. Behaviour is
--    unchanged; ALTER POLICY keeps every policy in place while rewriting it.
-- ============================================================================

REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;

ALTER POLICY profiles_select_own ON profiles USING ((select auth.uid()) = id);
ALTER POLICY profiles_insert_own ON profiles WITH CHECK ((select auth.uid()) = id);
ALTER POLICY profiles_update_own ON profiles USING ((select auth.uid()) = id);
ALTER POLICY profiles_delete_own ON profiles USING ((select auth.uid()) = id);

ALTER POLICY analyses_select_own ON analyses USING ((select auth.uid()) = user_id);
ALTER POLICY analyses_insert_own ON analyses WITH CHECK ((select auth.uid()) = user_id);
ALTER POLICY analyses_update_own ON analyses USING ((select auth.uid()) = user_id);
ALTER POLICY analyses_delete_own ON analyses USING ((select auth.uid()) = user_id);

ALTER POLICY analysis_assignments_select_own ON analysis_assignments
  USING (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));
ALTER POLICY analysis_assignments_insert_own ON analysis_assignments
  WITH CHECK (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));

ALTER POLICY risk_factors_select_own ON risk_factors
  USING (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));
ALTER POLICY risk_factors_insert_own ON risk_factors
  WITH CHECK (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));

ALTER POLICY priorities_select_own ON priorities
  USING (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));
ALTER POLICY priorities_insert_own ON priorities
  WITH CHECK (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));

ALTER POLICY recommendations_select_own ON recommendations
  USING (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));
ALTER POLICY recommendations_insert_own ON recommendations
  WITH CHECK (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));

ALTER POLICY recovery_plan_days_select_own ON recovery_plan_days
  USING (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));
ALTER POLICY recovery_plan_days_insert_own ON recovery_plan_days
  WITH CHECK (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));

ALTER POLICY recovery_plan_tasks_select_own ON recovery_plan_tasks
  USING (plan_day_id IN (
    SELECT rpd.id FROM recovery_plan_days rpd JOIN analyses a ON rpd.analysis_id = a.id
    WHERE a.user_id = (select auth.uid())
  ));
ALTER POLICY recovery_plan_tasks_insert_own ON recovery_plan_tasks
  WITH CHECK (plan_day_id IN (
    SELECT rpd.id FROM recovery_plan_days rpd JOIN analyses a ON rpd.analysis_id = a.id
    WHERE a.user_id = (select auth.uid())
  ));

ALTER POLICY explanations_select_own ON explanations
  USING (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));
ALTER POLICY explanations_insert_own ON explanations
  WITH CHECK (analysis_id IN (SELECT id FROM analyses WHERE user_id = (select auth.uid())));
