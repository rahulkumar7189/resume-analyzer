-- schema.sql
-- Run this script in your Supabase SQL Editor to initialize your database tables!

-- -------------------------------------------------------------
-- 1. Create Profiles Table (Role-Based Access Control)
-- -------------------------------------------------------------
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade primary key,
  full_name text,
  role text not null check (role in ('candidate', 'recruiter')),
  -- Recruiter Company Details
  company_name text,
  company_website text,
  company_industry text,
  company_size text,
  -- Candidate Personal Details
  phone_number text,
  gender text,
  dob text,
  location text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on profiles
alter table public.profiles enable row level security;

-- Create policies for profiles
create policy "Users can view their own profile" 
  on public.profiles for select 
  using (auth.uid() = id);

create policy "Users can update their own profile" 
  on public.profiles for update 
  using (auth.uid() = id);

create policy "Enable insert for authenticated users on signup" 
  on public.profiles for insert 
  with check (true);

-- -------------------------------------------------------------
-- 2. Create Resume Scans Table (ML Analysis Storage)
-- -------------------------------------------------------------
create table if not exists public.resume_scans (
  id bigint generated always as identity primary key,
  candidate_name text not null,
  candidate_email text not null,
  ats_score numeric(5,2) not null,
  extracted_skills jsonb not null default '{}'::jsonb,
  improvement_tips jsonb not null default '[]'::jsonb,
  job_description text,
  resume_url text,
  social_links jsonb not null default '{}'::jsonb,
  user_id uuid references auth.users default auth.uid(),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on resume_scans
alter table public.resume_scans enable row level security;

-- Create policies for resume_scans
-- Candidates can view only their own scans
-- Recruiters can view all scans
create policy "Candidates can view their own scans"
  on public.resume_scans for select
  using (
    auth.uid() = user_id or 
    exists (
      select 1 from public.profiles 
      where profiles.id = auth.uid() and profiles.role = 'recruiter'
    )
  );

create policy "Authenticated users can insert scans"
  on public.resume_scans for insert
  with check (auth.uid() is not null);
