-- ============================================================
-- ATS Platform — Supabase Migration  (fully idempotent — safe to re-run)
-- Run this in your Supabase SQL Editor (Dashboard → SQL Editor)
-- ============================================================

-- ── 1. Jobs table ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.jobs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recruiter_id  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title         TEXT NOT NULL,
  description   TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── 2. updated_at trigger (idempotent) ────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS jobs_set_updated_at ON public.jobs;
CREATE TRIGGER jobs_set_updated_at
  BEFORE UPDATE ON public.jobs
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ── 3. Add columns to resume_scans (idempotent) ───────────────────────────────
ALTER TABLE public.resume_scans
  ADD COLUMN IF NOT EXISTS job_id           UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS recruiter_id     UUID REFERENCES auth.users(id)  ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS experience_years NUMERIC(5,1) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS highest_degree   TEXT DEFAULT '',
  ADD COLUMN IF NOT EXISTS certifications   JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS domain           TEXT DEFAULT '',
  ADD COLUMN IF NOT EXISTS formatting       JSONB DEFAULT '{}';

-- ── 4. RLS — jobs table ───────────────────────────────────────────────────────
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "recruiter_select_own_jobs" ON public.jobs;
CREATE POLICY "recruiter_select_own_jobs"
  ON public.jobs FOR SELECT
  USING (auth.uid() = recruiter_id);

DROP POLICY IF EXISTS "recruiter_insert_own_jobs" ON public.jobs;
CREATE POLICY "recruiter_insert_own_jobs"
  ON public.jobs FOR INSERT
  WITH CHECK (auth.uid() = recruiter_id);

DROP POLICY IF EXISTS "recruiter_update_own_jobs" ON public.jobs;
CREATE POLICY "recruiter_update_own_jobs"
  ON public.jobs FOR UPDATE
  USING (auth.uid() = recruiter_id)
  WITH CHECK (auth.uid() = recruiter_id);

DROP POLICY IF EXISTS "recruiter_delete_own_jobs" ON public.jobs;
CREATE POLICY "recruiter_delete_own_jobs"
  ON public.jobs FOR DELETE
  USING (auth.uid() = recruiter_id);

-- ── 5. RLS — resume_scans table ───────────────────────────────────────────────
-- Note: The Python backend uses the SERVICE ROLE key which bypasses RLS.
-- These policies protect the anon / authenticated (client-side) roles.
ALTER TABLE public.resume_scans ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "recruiter_select_own_scans" ON public.resume_scans;
CREATE POLICY "recruiter_select_own_scans"
  ON public.resume_scans FOR SELECT
  USING (auth.uid() = recruiter_id OR recruiter_id IS NULL);

DROP POLICY IF EXISTS "recruiter_insert_own_scans" ON public.resume_scans;
CREATE POLICY "recruiter_insert_own_scans"
  ON public.resume_scans FOR INSERT
  WITH CHECK (auth.uid() = recruiter_id OR recruiter_id IS NULL);

DROP POLICY IF EXISTS "recruiter_update_own_scans" ON public.resume_scans;
CREATE POLICY "recruiter_update_own_scans"
  ON public.resume_scans FOR UPDATE
  USING (auth.uid() = recruiter_id OR recruiter_id IS NULL);

-- ── 6. Indexes (all idempotent via IF NOT EXISTS) ─────────────────────────────
CREATE INDEX IF NOT EXISTS idx_jobs_recruiter_id      ON public.jobs(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_resume_scans_job_id    ON public.resume_scans(job_id);
CREATE INDEX IF NOT EXISTS idx_resume_scans_recruiter ON public.resume_scans(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_resume_scans_score     ON public.resume_scans(ats_score DESC);
CREATE INDEX IF NOT EXISTS idx_resume_scans_email     ON public.resume_scans(candidate_email);
