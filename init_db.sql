-- init_db.sql
-- This script runs automatically when the Postgres Docker container is created.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── 1. Users Table (replaces Supabase auth.users) ──────────────────────────
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  salt TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── 2. Profiles Table ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
  full_name TEXT,
  role TEXT NOT NULL CHECK (role IN ('candidate', 'recruiter')),
  
  -- Recruiter Details
  company_name TEXT,
  company_website TEXT,
  company_industry TEXT,
  company_size TEXT,
  
  -- Extra fields
  title TEXT,
  portfolio_url TEXT,
  github_url TEXT,
  linkedin_url TEXT,
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── 3. Jobs Table ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  recruiter_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

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

-- ── 4. Resume Scans Table ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.resume_scans (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
  recruiter_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
  
  candidate_name TEXT NOT NULL,
  candidate_email TEXT NOT NULL,
  ats_score NUMERIC(5,2) NOT NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'shortlisted', 'interviewing', 'hired', 'rejected')),
  
  extracted_skills JSONB NOT NULL DEFAULT '{}'::jsonb,
  improvement_tips JSONB NOT NULL DEFAULT '[]'::jsonb,
  job_description TEXT,
  resume_url TEXT,
  social_links JSONB NOT NULL DEFAULT '{}'::jsonb,
  
  experience_years NUMERIC(5,1) DEFAULT 0,
  highest_degree TEXT DEFAULT '',
  certifications JSONB DEFAULT '[]',
  domain TEXT DEFAULT '',
  formatting JSONB DEFAULT '{}',
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── 5. Indexes ───────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_jobs_recruiter_id      ON public.jobs(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_resume_scans_job_id    ON public.resume_scans(job_id);
CREATE INDEX IF NOT EXISTS idx_resume_scans_recruiter ON public.resume_scans(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_resume_scans_score     ON public.resume_scans(ats_score DESC);
CREATE INDEX IF NOT EXISTS idx_resume_scans_email     ON public.resume_scans(candidate_email);
