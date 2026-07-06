'use server'

import { query } from '@/lib/db'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export async function getProfile() {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return null

  const { rows } = await query(`
    SELECT p.*, u.two_factor_enabled, u.two_factor_method 
    FROM profiles p 
    JOIN users u ON p.id = u.id 
    WHERE p.id = $1
  `, [session.user.id])
  return rows[0] || null
}

export async function saveProfile(data: any) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return { error: 'Not authenticated' }

  try {
    await query(`
      INSERT INTO profiles (id, full_name, title, company_name, company_website, company_industry, company_size, portfolio_url, github_url, linkedin_url, role)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, COALESCE((SELECT role FROM profiles WHERE id = $1), 'candidate'))
      ON CONFLICT (id) DO UPDATE SET
        full_name = EXCLUDED.full_name,
        title = EXCLUDED.title,
        company_name = EXCLUDED.company_name,
        company_website = EXCLUDED.company_website,
        company_industry = EXCLUDED.company_industry,
        company_size = EXCLUDED.company_size,
        portfolio_url = EXCLUDED.portfolio_url,
        github_url = EXCLUDED.github_url,
        linkedin_url = EXCLUDED.linkedin_url
    `, [
      session.user.id,
      data.fullName || '',
      data.title || '',
      data.companyName || '',
      data.companyWebsite || '',
      data.companyIndustry || '',
      data.companySize || '',
      data.portfolioUrl || '',
      data.githubUrl || '',
      data.linkedinUrl || ''
    ])
    return { success: true }
  } catch (error: any) {
    return { error: error.message }
  }
}

export async function getCandidateHistory(email: string) {
  const { rows } = await query('SELECT * FROM resume_scans WHERE candidate_email = $1 ORDER BY created_at DESC', [email])
  return rows
}

// ── Recruiter Actions ───────────────────────────────────────────────────────

export async function getJobs() {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return []

  const { rows } = await query('SELECT * FROM jobs WHERE recruiter_id = $1 ORDER BY created_at DESC', [session.user.id])
  return rows
}

export async function createJob(title: string, description: string) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return { error: 'Not authenticated' }

  try {
    const { rows } = await query(
      'INSERT INTO jobs (recruiter_id, title, description) VALUES ($1, $2, $3) RETURNING *',
      [session.user.id, title, description]
    )
    return { data: rows[0] }
  } catch (error: any) {
    return { error: error.message }
  }
}

export async function updateJob(jobId: string, title: string, description: string) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return { error: 'Not authenticated' }

  try {
    await query(
      'UPDATE jobs SET title = $1, description = $2, updated_at = now() WHERE id = $3 AND recruiter_id = $4',
      [title, description, jobId, session.user.id]
    )
    return { success: true }
  } catch (error: any) {
    return { error: error.message }
  }
}

export async function deleteJob(jobId: string) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return { error: 'Not authenticated' }

  try {
    await query('DELETE FROM jobs WHERE id = $1 AND recruiter_id = $2', [jobId, session.user.id])
    return { success: true }
  } catch (error: any) {
    return { error: error.message }
  }
}

export async function getCandidatesForJob(jobId: string) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return []

  const { rows } = await query(
    'SELECT * FROM resume_scans WHERE job_id = $1 ORDER BY ats_score DESC',
    [jobId]
  )
  return rows
}

export async function deleteCandidate(candidateId: string | number) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return { error: 'Not authenticated' }

  try {
    await query('DELETE FROM resume_scans WHERE id = $1 AND recruiter_id = $2', [candidateId, session.user.id])
    return { success: true }
  } catch (error: any) {
    return { error: error.message }
  }
}

export async function updateCandidateStatus(candidateId: string | number, newStatus: string) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) return { error: 'Not authenticated' }

  try {
    await query(
      'UPDATE resume_scans SET status = $1 WHERE id = $2 AND recruiter_id = $3', 
      [newStatus, candidateId, session.user.id]
    )
    return { success: true }
  } catch (error: any) {
    return { error: error.message }
  }
}
