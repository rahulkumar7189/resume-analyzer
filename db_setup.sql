-- db_setup.sql
-- Run this script to initialize the local PostgreSQL database

-- -------------------------------------------------------------
-- 1. Create Users Table (Authentication)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  salt TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -------------------------------------------------------------
-- 2. Create Profiles Table (Role-Based Access Control)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
  full_name TEXT,
  role TEXT NOT NULL CHECK (role IN ('candidate', 'recruiter')),
  
  -- Recruiter Company Details
  company_name TEXT,
  company_website TEXT,
  company_industry TEXT,
  company_size TEXT,
  
  -- Candidate Personal Details
  phone_number TEXT,
  gender TEXT,
  dob TEXT,
  location TEXT,
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -------------------------------------------------------------
-- 3. Create Jobs table
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recruiter_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -------------------------------------------------------------
-- 4. Create Resume Scans Table (ML Analysis Storage)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.resume_scans (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  candidate_name TEXT NOT NULL,
  candidate_email TEXT NOT NULL,
  ats_score NUMERIC(5,2) NOT NULL,
  extracted_skills JSONB NOT NULL DEFAULT '{}'::jsonb,
  improvement_tips JSONB NOT NULL DEFAULT '[]'::jsonb,
  job_description TEXT,
  resume_url TEXT,
  social_links JSONB NOT NULL DEFAULT '{}'::jsonb,
  user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
  job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
  recruiter_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
  experience_years NUMERIC(5,1) DEFAULT 0,
  highest_degree TEXT DEFAULT '',
  certifications JSONB DEFAULT '[]',
  domain TEXT DEFAULT '',
  formatting JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -------------------------------------------------------------
-- 5. Updated At Triggers
-- -------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS profiles_set_updated_at ON public.profiles;
CREATE TRIGGER profiles_set_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS jobs_set_updated_at ON public.jobs;
CREATE TRIGGER jobs_set_updated_at
  BEFORE UPDATE ON public.jobs
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- -------------------------------------------------------------
-- 6. Indexes
-- -------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_jobs_recruiter_id ON public.jobs(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_resume_scans_job_id ON public.resume_scans(job_id);
CREATE INDEX IF NOT EXISTS idx_resume_scans_recruiter ON public.resume_scans(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_resume_scans_score ON public.resume_scans(ats_score DESC);
CREATE INDEX IF NOT EXISTS idx_resume_scans_email ON public.resume_scans(candidate_email);
