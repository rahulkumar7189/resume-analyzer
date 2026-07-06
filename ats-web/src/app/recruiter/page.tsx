'use client'

import { useState, useEffect, useRef } from 'react'
import {
  UploadCloud, Users, Search, LogOut, Plus, X,
  Loader2, User, Building2, Briefcase, ChevronRight, Pencil,
  Trash2, CheckCircle2, AlertCircle, Clock, FileText, Zap, BarChart, FileWarning, XCircle,
  Sun, Moon, Menu, LayoutTemplate, List
} from 'lucide-react'
import { useSession, signOut } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import { getProfile, saveProfile as saveProfileAction, getJobs, createJob, updateJob, deleteJob, getCandidatesForJob, deleteCandidate, updateCandidateStatus } from '../actions'
import { useToast } from '@/components/ui/ToastProvider'
import TwoFactorSetup from '@/components/TwoFactorSetup'

// ── Types ─────────────────────────────────────────────────────────────────────

type Job = {
  id: string
  title: string
  description: string
  created_at?: string
}

type FileProgress = {
  filename: string
  status: 'pending' | 'processing' | 'done' | 'error'
  error?: string
}

type Candidate = {
  id: string
  jobId: string
  name: string
  email: string
  score: number
  missing: string[]
  matched: string[]
  resumeUrl: string | null
  socialLinks: Record<string, string>
  experienceYears?: number
  highestDegree?: string
  domain?: string
  formatting?: any
  tips?: any[]
  createdAt?: string
  status: string
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function RecruiterDashboard() {
  const { theme, setTheme } = useTheme()
  const [files, setFiles] = useState<File[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [jobsLoading, setJobsLoading] = useState(true)
  const [activeJobId, setActiveJobId] = useState<string>('')
  const [showModal, setShowModal] = useState(false)
  const [newJobTitle, setNewJobTitle] = useState('')
  const [newJobDesc, setNewJobDesc] = useState('')
  const [jobSaving, setJobSaving] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [fileProgress, setFileProgress] = useState<FileProgress[]>([])
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [candidatesLoading, setCandidatesLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'profile'>('dashboard')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list')
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  // Edit job state
  const [showEditModal, setShowEditModal] = useState(false)
  const [editJobTitle, setEditJobTitle] = useState('')
  const [editJobDesc, setEditJobDesc] = useState('')
  const [editSaving, setEditSaving] = useState(false)

  const [profile, setProfile] = useState({
    fullName: '', companyName: '', companyWebsite: '',
    companyIndustry: '', companySize: '',
    twoFactorEnabled: false, twoFactorMethod: null as string | null
  })
  const [saveLoading, setSaveLoading] = useState(false)
  const { data: session, status } = useSession()
  const router = useRouter()
  const { addToast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const activeJob = jobs.find(j => j.id === activeJobId) || jobs[0]

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login')
    } else if (status === 'authenticated' && (session?.user as any)?.role !== 'recruiter') {
      addToast('Unauthorized access. Redirecting to your dashboard.', 'error')
      router.push('/candidate')
    }
  }, [status, session, router, addToast])

  // ── Load profile ───────────────────────────────────────────────────────────
  useEffect(() => {
    async function loadProfile() {
      if (!session?.user) return
      const data = await getProfile()
      if (data) {
        setProfile({
          fullName: data.full_name || '',
          companyName: data.company_name || '',
          companyWebsite: data.company_website || '',
          companyIndustry: data.company_industry || '',
          companySize: data.company_size || '',
          twoFactorEnabled: data.two_factor_enabled || false,
          twoFactorMethod: data.two_factor_method || null
        })
      }
    }
    loadProfile()
  }, [session])

  // ── Load jobs from Supabase on mount ───────────────────────────────────────
  useEffect(() => {
    loadJobs()
  }, [session])

  const loadJobs = async () => {
    setJobsLoading(true)
    try {
      if (!session?.user) return
      const data = await getJobs()
      
      setJobs(data || [])
      if (data && data.length > 0) {
        setActiveJobId(prev => prev || data[0].id)
      }
    } finally {
      setJobsLoading(false)
    }
  }

  // ── Load candidates from Supabase when active job changes ──────────────────
  useEffect(() => {
    if (!activeJobId) return
    loadCandidatesForJob(activeJobId)
    setSelectedCandidate(null)
  }, [activeJobId])

  const loadCandidatesForJob = async (jobId: string) => {
    setCandidatesLoading(true)
    try {
      const data = await getCandidatesForJob(jobId)

      const mapped: Candidate[] = (data || []).map((row: any) => ({
        id: row.id,
        jobId: row.job_id,
        name: row.candidate_name || 'Unknown',
        email: row.candidate_email || '',
        score: row.ats_score || 0,
        missing: row.extracted_skills?.missing || [],
        matched: row.extracted_skills?.matched || [],
        resumeUrl: row.resume_url || null,
        socialLinks: row.social_links || {},
        experienceYears: row.experience_years,
        highestDegree: row.highest_degree,
        domain: row.domain,
        formatting: row.formatting,
        tips: row.improvement_tips || [],
        createdAt: row.created_at,
        status: row.status || 'new'
      }))
      setCandidates(mapped)
    } finally {
      setCandidatesLoading(false)
    }
  }

  const handleDeleteCandidate = async (e: React.MouseEvent, candidateId: string | number) => {
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this candidate?')) return

    const res = await deleteCandidate(candidateId)
    if (res.error) {
      addToast(res.error, 'error')
    } else {
      addToast('Candidate deleted successfully', 'success')
      if (activeJobId) loadCandidatesForJob(activeJobId)
      if (selectedCandidate?.id === candidateId) setSelectedCandidate(null)
    }
  }

  const handleStatusChange = async (candidateId: string | number, newStatus: string) => {
    setCandidates(prev => prev.map(c => c.id === candidateId ? { ...c, status: newStatus } : c))
    const res = await updateCandidateStatus(candidateId, newStatus)
    if (res.error) {
      addToast('Failed to update status: ' + res.error, 'error')
      if (activeJobId) loadCandidatesForJob(activeJobId) // revert
    } else {
      addToast('Status updated to ' + newStatus, 'success')
    }
  }

  const handleDragStart = (e: React.DragEvent, candidateId: string) => {
    e.dataTransfer.setData('candidateId', candidateId)
  }
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault() }
  const handleDrop = (e: React.DragEvent, newStatus: string) => {
    const candidateId = e.dataTransfer.getData('candidateId')
    if (candidateId) handleStatusChange(candidateId, newStatus)
  }

  // ── Profile save ───────────────────────────────────────────────────────────
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaveLoading(true)
    const result = await saveProfileAction(profile)
    if (result.error) addToast('Error saving profile: ' + result.error, 'error')
    else addToast('Profile saved successfully!', 'success')
    setSaveLoading(false)
  }

  const handleLogout = async () => {
    await signOut({ callbackUrl: '/login' })
  }

  // ── Job CRUD ──────────────────────────────────────────────────────────────
  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault()
    setJobSaving(true)
    try {
      const res = await createJob(newJobTitle, newJobDesc)
      if (res.error) {
        addToast('Failed to create job: ' + res.error, 'error')
      } else if (res.data) {
        setJobs(prev => [res.data, ...prev])
        setActiveJobId(res.data.id)
        setShowModal(false)
        setNewJobTitle('')
        setNewJobDesc('')
        setFiles([])
        addToast('Job created successfully', 'success')
      }
    } finally {
      setJobSaving(false)
    }
  }

  const handleOpenEdit = () => {
    if (!activeJob) return
    setEditJobTitle(activeJob.title)
    setEditJobDesc(activeJob.description)
    setShowEditModal(true)
  }

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeJob) return
    setEditSaving(true)
    try {
      const res = await updateJob(activeJob.id, editJobTitle, editJobDesc)
      if (res.error) {
        addToast('Failed to update job: ' + res.error, 'error')
      } else {
        setJobs(jobs.map(j =>
          j.id === activeJobId ? { ...j, title: editJobTitle, description: editJobDesc } : j
        ))
        setShowEditModal(false)
        addToast('Job updated successfully', 'success')
      }
    } finally {
      setEditSaving(false)
    }
  }

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('Delete this job post? All linked candidate scans will be unlinked (not deleted).')) return
    const res = await deleteJob(jobId)
    if (res.error) { addToast('Failed to delete job: ' + res.error, 'error'); return }
    const remaining = jobs.filter(j => j.id !== jobId)
    setJobs(remaining)
    if (remaining.length > 0) setActiveJobId(remaining[0].id)
    setCandidates(prev => prev.filter(c => c.jobId !== jobId))
    addToast('Job deleted', 'success')
  }

  // ── Bulk upload with per-file progress ────────────────────────────────────
  const handleProcessFiles = async () => {
    if (files.length === 0 || !activeJob) return
    setProcessing(true)

    // Initialise progress state for each file
    const progress: FileProgress[] = files.map(f => ({ filename: f.name, status: 'pending' }))
    setFileProgress(progress)

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      setFileProgress(prev => prev.map((p, idx) => idx === i ? { ...p, status: 'processing' } : p))

      const formData = new FormData()
      formData.append('resume', file)
      formData.append('job_description', activeJob.description)
      if (activeJob.id) formData.append('job_id', activeJob.id)
      if (session?.user?.id) formData.append('recruiter_id', session.user.id)

      try {
        const res = await fetch('/api/analyze', {
          method: 'POST',
          body: formData
        })

        if (!res.ok) throw new Error(`Server returned ${res.status}: ${res.statusText}`)

        const data = await res.json()
        if (data.status === 'queued') {
          const taskId = data.task_id;
          let isComplete = false;
          while (!isComplete) {
            await new Promise(r => setTimeout(r, 2000));
            const pollRes = await fetch(`/api/task/${taskId}`);
            const pollData = await pollRes.json();
            
            if (pollData.status === 'success') {
              setFileProgress(prev => prev.map((p, idx) => idx === i ? { ...p, status: 'done' } : p))
              isComplete = true;
            } else if (pollData.status === 'error') {
              throw new Error(pollData.detail || 'Error analyzing resume.')
            }
          }
        } else if (data.status === 'success') {
          setFileProgress(prev => prev.map((p, idx) => idx === i ? { ...p, status: 'done' } : p))
        } else {
          throw new Error(data.detail || 'Unknown API error')
        }
      } catch (err: any) {
        const msg = err?.message || 'Request failed'
        setFileProgress(prev => prev.map((p, idx) =>
          idx === i ? { ...p, status: 'error', error: msg } : p
        ))
      }
    }

    // Refresh candidate list to pull the newly inserted candidates from DB
    await loadCandidatesForJob(activeJob.id)
    
    setFiles([])
    if (fileInputRef.current) fileInputRef.current.value = ''
    setProcessing(false)
    addToast('Batch processing complete', 'info')
  }

  // ── Derived state ──────────────────────────────────────────────────────────
  const jobCandidates = candidates
    .filter(c => c.jobId === activeJob?.id)
    .filter(c =>
      !searchQuery ||
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.email.toLowerCase().includes(searchQuery.toLowerCase())
    )

  const progressDone = fileProgress.filter(p => p.status === 'done').length
  const progressError = fileProgress.filter(p => p.status === 'error').length
  const progressTotal = fileProgress.length

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-500/20 text-green-400 border-green-500/30'
    if (score >= 60) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
    return 'bg-red-500/20 text-red-400 border-red-500/30'
  }

  const getProgressIcon = (status: FileProgress['status']) => {
    if (status === 'done') return <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0" />
    if (status === 'error') return <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
    if (status === 'processing') return <Loader2 className="w-5 h-5 text-primary animate-spin shrink-0" />
    return <Clock className="w-5 h-5 text-foreground/50 shrink-0" />
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="h-screen bg-grid-pattern flex relative overflow-hidden text-foreground">

      {/* EDIT JOB MODAL */}
      {showEditModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
          <div className="bg-background border border-border rounded-3xl w-full max-w-2xl shadow-2xl animate-slide-in-bottom overflow-hidden">
            <div className="flex justify-between items-center p-8 border-b border-border bg-surface hover:bg-surface-hover">
              <div>
                <h2 className="text-2xl font-extrabold text-foreground">Edit Job Post</h2>
                <p className="text-foreground/60 text-sm mt-1">Update the title or description of this position.</p>
              </div>
              <button onClick={() => setShowEditModal(false)} className="text-foreground/60 hover:text-foreground transition-colors bg-surface hover:bg-surface-hover hover:bg-surface-hover p-2 rounded-xl border border-border">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSaveEdit} className="p-8 space-y-6">
              <div>
                <label className="block text-sm font-bold text-foreground/80 mb-2">Job Title</label>
                <input type="text" required value={editJobTitle} onChange={e => setEditJobTitle(e.target.value)}
                  className="w-full bg-surface border-border border border-border rounded-xl p-4 text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all placeholder-gray-600" />
              </div>
              <div>
                <label className="block text-sm font-bold text-foreground/80 mb-2">Job Description</label>
                <textarea required value={editJobDesc} onChange={e => setEditJobDesc(e.target.value)}
                  className="w-full h-48 bg-surface border-border border border-border rounded-xl p-4 text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all resize-none custom-scrollbar" />
              </div>
              <div className="flex justify-end pt-4 gap-3 border-t border-border">
                <button type="button" onClick={() => setShowEditModal(false)} className="px-6 py-3 rounded-xl text-foreground/60 hover:text-foreground border border-transparent hover:bg-surface hover:bg-surface-hover transition-all font-semibold">Cancel</button>
                <button type="submit" disabled={editSaving} className="bg-primary hover:bg-blue-600 disabled:bg-gray-800 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)] flex items-center gap-2">
                  {editSaving && <Loader2 className="w-4 h-4 animate-spin" />}
                  {editSaving ? 'Saving…' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CREATE JOB MODAL */}
      {showModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
          <div className="bg-background border border-border rounded-3xl w-full max-w-2xl shadow-2xl animate-slide-in-bottom overflow-hidden">
            <div className="flex justify-between items-center p-8 border-b border-border bg-surface hover:bg-surface-hover">
              <div>
                <h2 className="text-2xl font-extrabold text-foreground">Create New Job Post</h2>
                <p className="text-foreground/60 text-sm mt-1">Add a title and description to start parsing resumes.</p>
              </div>
              <button onClick={() => setShowModal(false)} className="text-foreground/60 hover:text-foreground transition-colors bg-surface hover:bg-surface-hover hover:bg-surface-hover p-2 rounded-xl border border-border">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateJob} className="p-8 space-y-6">
              <div>
                <label className="block text-sm font-bold text-foreground/80 mb-2">Job Title</label>
                <input type="text" required value={newJobTitle} onChange={e => setNewJobTitle(e.target.value)}
                  placeholder="e.g. Senior Machine Learning Engineer"
                  className="w-full bg-surface border-border border border-border rounded-xl p-4 text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all placeholder-gray-600" />
              </div>
              <div>
                <label className="block text-sm font-bold text-foreground/80 mb-2">Job Description</label>
                <textarea required value={newJobDesc} onChange={e => setNewJobDesc(e.target.value)}
                  placeholder="Paste the full job description here…"
                  className="w-full h-48 bg-surface border-border border border-border rounded-xl p-4 text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all resize-none custom-scrollbar placeholder-gray-600" />
              </div>
              <div className="flex justify-end pt-4 gap-3 border-t border-border">
                <button type="button" onClick={() => setShowModal(false)} className="px-6 py-3 rounded-xl text-foreground/60 hover:text-foreground border border-transparent hover:bg-surface hover:bg-surface-hover transition-all font-semibold">Cancel</button>
                <button type="submit" disabled={jobSaving} className="bg-primary hover:bg-blue-600 disabled:bg-gray-800 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)] flex items-center gap-2">
                  {jobSaving && <Loader2 className="w-4 h-4 animate-spin" />}
                  {jobSaving ? 'Saving…' : 'Save & Set Active'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MOBILE DRAWER OVERLAY */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden animate-fade-in"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* SIDEBAR */}
      <aside className={`fixed inset-y-0 left-0 w-72 bg-surface border-r border-border flex flex-col p-6 z-50 transform transition-transform duration-300 lg:relative lg:translate-x-0 ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="mb-8 px-2 flex items-center space-x-3">
          <div className="w-10 h-10 bg-secondary/20 rounded-xl border border-secondary/30 flex items-center justify-center">
            <Building2 className="w-5 h-5 text-secondary" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight">NeuroATS</h1>
            <p className="text-xs text-foreground/60">Recruiter Portal</p>
          </div>
          <div className="ml-auto">
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-full hover:bg-surface-hover transition-colors text-foreground/70 hover:text-foreground"
            >
              {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>
        </div>

        <div className="space-y-2 mb-8">
          <button onClick={() => setActiveTab('dashboard')} className={`w-full text-left px-4 py-3.5 rounded-xl transition-all text-sm font-semibold flex items-center space-x-3 ${activeTab === 'dashboard' ? 'bg-secondary/10 text-foreground border border-secondary/25 shadow-inner' : 'text-foreground/60 hover:text-foreground hover:bg-surface hover:bg-surface-hover border border-transparent'}`}>
            <Briefcase className={`w-5 h-5 ${activeTab === 'dashboard' ? 'text-secondary' : 'text-foreground/50'}`} />
            <span>Job Dashboard</span>
          </button>
          <button onClick={() => setActiveTab('profile')} className={`w-full text-left px-4 py-3.5 rounded-xl transition-all text-sm font-semibold flex items-center space-x-3 ${activeTab === 'profile' ? 'bg-secondary/10 text-foreground border border-secondary/25' : 'text-foreground/60 hover:text-foreground hover:bg-surface hover:bg-surface-hover border border-transparent'}`}>
            <Building2 className={`w-5 h-5 ${activeTab === 'profile' ? 'text-secondary' : 'text-foreground/50'}`} />
            <span>Company Profile</span>
          </button>
        </div>

        {/* Job Posts List */}
        {activeTab === 'dashboard' && (
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2 relative">
            <div className="flex items-center justify-between px-2 mb-4">
              <p className="text-xs font-bold text-foreground/50 uppercase tracking-widest">Active Jobs</p>
              {jobsLoading && <Loader2 className="w-4 h-4 text-foreground/50 animate-spin" />}
            </div>

            {!jobsLoading && jobs.length === 0 && (
              <div className="text-center py-10 px-4 bg-surface hover:bg-surface-hover border border-dashed border-border rounded-2xl">
                <Briefcase className="w-8 h-8 text-foreground/40 mx-auto mb-3" />
                <p className="text-sm text-foreground/60 font-medium">No job posts yet.</p>
                <button onClick={() => setShowModal(true)} className="text-sm text-secondary font-bold hover:underline mt-2">Create one →</button>
              </div>
            )}

            {jobs.map(job => {
              const isActive = job.id === activeJobId
              return (
                <div key={job.id} className={`w-full rounded-2xl transition-all text-sm border overflow-hidden ${isActive ? 'bg-secondary/10 border-secondary/30 shadow-lg shadow-secondary/5' : 'bg-surface hover:bg-surface-hover border-border hover:bg-surface-hover hover:border-border'}`}>
                  <button onClick={() => { setActiveJobId(job.id); setFiles([]); setSelectedCandidate(null) }} className="w-full text-left px-4 py-4 flex items-center justify-between group">
                    <div className="min-w-0 pr-2">
                      <span className={`font-bold block truncate ${isActive ? 'text-foreground text-base' : 'text-foreground/60 group-hover:text-gray-200'}`}>{job.title}</span>
                      {isActive && <span className="text-xs text-secondary font-medium mt-1 inline-block">Active Selection</span>}
                    </div>
                    {!isActive && <ChevronRight className="w-4 h-4 shrink-0 text-foreground/40 group-hover:text-foreground/60 transition-transform group-hover:translate-x-1" />}
                  </button>
                  {isActive && (
                    <div className="flex items-center gap-2 px-4 pb-4 pt-1">
                      <button onClick={handleOpenEdit} className="flex-1 flex items-center justify-center gap-1.5 text-xs text-foreground/80 hover:text-foreground bg-surface hover:bg-surface-hover hover:bg-surface-hover py-2 rounded-xl border border-border transition-all font-semibold">
                        <Pencil className="w-3.5 h-3.5" /> Edit
                      </button>
                      <button onClick={() => handleDeleteJob(job.id)} className="flex items-center justify-center gap-1.5 text-xs text-red-400/80 hover:text-foreground bg-red-500/10 hover:bg-red-500/30 py-2 px-3 rounded-xl border border-red-500/20 hover:border-red-500/40 transition-all font-semibold" title="Delete Job">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        <div className="mt-8 pt-6 border-t border-border space-y-3 shrink-0">
          <button onClick={() => setShowModal(true)} className="w-full bg-surface hover:bg-surface-hover hover:bg-surface-hover text-foreground px-4 py-3 rounded-xl border border-border font-bold text-sm transition-all flex items-center justify-center hover:border-border">
            <Plus className="w-4 h-4 mr-2" /> New Job Post
          </button>
          <button onClick={handleLogout} className="w-full text-left px-4 py-3 rounded-xl transition-all text-sm font-semibold flex items-center justify-center space-x-2 text-red-400/80 hover:text-red-400 hover:bg-red-500/10 border border-transparent">
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 overflow-y-auto custom-scrollbar relative flex flex-col w-full">
        <div className="absolute inset-0 bg-gradient-to-b from-secondary/5 to-transparent pointer-events-none h-96" />
        
        {/* Mobile Header (Hidden on Desktop) */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b border-border bg-surface/50 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-secondary/20 rounded-lg border border-secondary/30 flex items-center justify-center">
              <Building2 className="w-4 h-4 text-secondary" />
            </div>
            <span className="font-bold text-foreground">NeuroATS</span>
          </div>
          <button 
            onClick={() => setIsMobileMenuOpen(true)}
            className="p-2 -mr-2 text-foreground/70 hover:text-foreground"
          >
            <Menu className="w-6 h-6" />
          </button>
        </div>

        {/* Dashboard Content */}
        <div className={`flex-1 transition-all duration-300 w-full ${selectedCandidate ? 'lg:pr-[30rem]' : ''}`}>
          <div className="max-w-6xl mx-auto px-4 lg:px-10 py-6 lg:py-12 space-y-8 relative z-10 w-full">
            {activeTab === 'dashboard' ? (
              <div className="animate-fade-in space-y-8">
                {activeJob ? (
                  <>
                    <header className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-border pb-6 gap-6">
                      <div className="max-w-3xl pr-8">
                        <p className="text-xs font-bold text-secondary uppercase tracking-widest mb-2">Active Job</p>
                        <h2 className="text-4xl font-extrabold text-foreground tracking-tight mb-2">{activeJob.title}</h2>
                        <p className="text-foreground/60 text-sm leading-relaxed line-clamp-2">{activeJob.description}</p>
                      </div>
                      <div className="flex flex-row md:flex-col items-center md:items-end gap-4 shrink-0">
                        <div className="bg-surface border border-border p-1 rounded-lg flex items-center shadow-sm">
                          <button 
                            onClick={() => setViewMode('list')} 
                            className={`p-2 rounded-md flex items-center transition-all ${viewMode === 'list' ? 'bg-secondary/20 text-secondary' : 'text-foreground/50 hover:text-foreground'}`}
                            title="List View"
                          >
                            <List className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => setViewMode('kanban')} 
                            className={`p-2 rounded-md flex items-center transition-all ${viewMode === 'kanban' ? 'bg-secondary/20 text-secondary' : 'text-foreground/50 hover:text-foreground'}`}
                            title="Kanban View"
                          >
                            <LayoutTemplate className="w-4 h-4" />
                          </button>
                        </div>
                        <div className="bg-secondary/10 border border-secondary/20 px-6 py-3 rounded-2xl text-center">
                          <span className="block text-2xl font-black text-secondary">{jobCandidates.length}</span>
                          <span className="text-xs text-foreground/60 font-bold uppercase tracking-wider">Candidates</span>
                        </div>
                      </div>
                    </header>

                    {/* Bulk Upload Zone */}
                    <div className="bg-surface border border-border rounded-3xl p-8 backdrop-blur-xl shadow-xl flex flex-col items-center">
                      <div className="w-full max-w-2xl text-center">
                        <h3 className="text-lg font-bold text-foreground mb-2">Process Resumes</h3>
                        <p className="text-sm text-foreground/60 mb-6">Upload PDFs, DOCX, or TXT files to bulk parse against this job description.</p>
                        
                        <div className="flex gap-4 mb-4">
                          <div className="flex-1 relative group cursor-pointer">
                            <input type="file" multiple className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" accept=".pdf,.docx,.txt" onChange={e => setFiles(Array.from(e.target.files || []))} ref={fileInputRef} />
                            <div className={`h-full border-2 border-dashed rounded-2xl flex items-center justify-center p-4 transition-all ${files.length > 0 ? 'border-secondary/50 bg-secondary/10' : 'border-border bg-surface border-border group-hover:border-secondary/30 group-hover:bg-surface hover:bg-surface-hover'}`}>
                              {files.length > 0 ? (
                                <span className="font-bold text-secondary">{files.length} file(s) selected</span>
                              ) : (
                                <span className="text-foreground/60 font-medium flex items-center"><UploadCloud className="w-5 h-5 mr-2 opacity-50" /> Select multiple resumes</span>
                              )}
                            </div>
                          </div>
                          <button onClick={handleProcessFiles} disabled={files.length === 0 || processing} className="bg-secondary hover:bg-purple-600 disabled:bg-gray-800 text-white px-8 py-4 rounded-2xl font-bold transition-all shadow-lg hover:shadow-secondary/30 disabled:shadow-none flex items-center justify-center whitespace-nowrap min-w-[200px]">
                            {processing ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Zap className="w-5 h-5 mr-2" />}
                            {processing ? 'Processing...' : 'Run Pipeline'}
                          </button>
                        </div>

                        {/* Progress UI */}
                        {fileProgress.length > 0 && (
                          <div className="w-full mt-6 bg-surface border-border border border-border rounded-2xl p-6 text-left animate-slide-in-bottom">
                            <div className="flex justify-between text-sm font-bold mb-4 border-b border-border pb-2">
                              <span className="text-foreground">Batch Status</span>
                              <span className="text-foreground/60">
                                {progressDone} done, {progressError} errors / {progressTotal} total
                              </span>
                            </div>
                            <div className="max-h-48 overflow-y-auto custom-scrollbar pr-2 space-y-2">
                              {fileProgress.map((p, i) => (
                                <div key={i} className="flex items-center justify-between bg-surface hover:bg-surface-hover px-4 py-3 rounded-xl border border-border">
                                  <div className="flex items-center overflow-hidden pr-4">
                                    {getProgressIcon(p.status)}
                                    <span className={`ml-3 text-sm truncate font-medium ${p.status === 'error' ? 'text-red-400' : 'text-foreground/80'}`}>{p.filename}</span>
                                  </div>
                                  {p.error && <span className="text-xs text-red-400 bg-red-500/10 px-2 py-1 rounded truncate max-w-[200px]" title={p.error}>{p.error}</span>}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Candidates Table */}
                    <div className="bg-surface border border-border rounded-3xl backdrop-blur-xl shadow-xl overflow-hidden flex flex-col min-h-[500px]">
                      <div className="p-6 border-b border-border flex justify-between items-center bg-surface hover:bg-surface-hover">
                        <div className="flex items-center gap-4">
                          <h3 className="text-lg font-extrabold text-foreground flex items-center"><Users className="w-5 h-5 mr-3 text-secondary" /> Ranked Candidates</h3>
                          <div className="flex bg-black/20 border border-border rounded-lg overflow-hidden">
                            <button onClick={() => setViewMode('list')} className={`px-4 py-1.5 text-xs font-bold transition-colors ${viewMode === 'list' ? 'bg-secondary text-white' : 'text-foreground/60 hover:text-foreground hover:bg-black/20'}`}>List</button>
                            <button onClick={() => setViewMode('kanban')} className={`px-4 py-1.5 text-xs font-bold transition-colors ${viewMode === 'kanban' ? 'bg-secondary text-white' : 'text-foreground/60 hover:text-foreground hover:bg-black/20'}`}>Kanban</button>
                          </div>
                        </div>
                        <div className="relative">
                          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-foreground/50" />
                          <input type="text" placeholder="Search names or emails..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="bg-surface border-border border border-border rounded-xl pl-9 pr-4 py-2 text-sm text-foreground focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all w-64" />
                        </div>
                      </div>

                      {candidatesLoading ? (
                        <div className="p-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-secondary" /></div>
                      ) : jobCandidates.length > 0 ? (
                        viewMode === 'list' ? (
                          <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                              <thead>
                                <tr className="bg-black/5 dark:bg-black/20 text-foreground/60 text-xs uppercase tracking-wider font-bold">
                                  <th className="p-4 pl-6 font-semibold">Score</th>
                                  <th className="p-4 font-semibold">Candidate</th>
                                  <th className="p-4 font-semibold">Status</th>
                                  <th className="p-4 font-semibold">Experience</th>
                                  <th className="p-4 font-semibold">Domain & Degree</th>
                                  <th className="p-4 font-semibold">Major Missing Skills</th>
                                  <th className="p-4 pr-6 text-right font-semibold">Action</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-border">
                                {jobCandidates.map(c => (
                                  <tr key={c.id} 
                                      onClick={() => setSelectedCandidate(c)}
                                      className={`hover:hover:bg-foreground/5 transition-colors cursor-pointer ${selectedCandidate?.id === c.id ? 'bg-secondary/5 border-l-4 border-secondary' : 'border-l-4 border-transparent'}`}>
                                    <td className="p-4 pl-6 w-24">
                                      <div className={`font-black text-lg px-3 py-1.5 rounded-lg text-center border ${getScoreColor(c.score)}`}>{c.score}%</div>
                                    </td>
                                    <td className="p-4">
                                      <div className="font-bold text-foreground mb-0.5">{c.name}</div>
                                      <div className="text-xs text-foreground/50">{c.email}</div>
                                    </td>
                                    <td className="p-4">
                                      <select 
                                        value={c.status} 
                                        onChange={(e) => { e.stopPropagation(); handleStatusChange(c.id, e.target.value); }}
                                        className="bg-black/10 border border-border rounded-md text-xs font-bold uppercase tracking-wider px-2 py-1 text-foreground focus:outline-none"
                                      >
                                        <option value="new">New</option>
                                        <option value="shortlisted">Shortlisted</option>
                                        <option value="interviewing">Interviewing</option>
                                        <option value="hired">Hired</option>
                                        <option value="rejected">Rejected</option>
                                      </select>
                                    </td>
                                    <td className="p-4">
                                      <span className="bg-surface hover:bg-surface-hover border border-border px-2.5 py-1 rounded-md text-xs font-semibold text-foreground/80">
                                        {c.experienceYears || 0} years
                                      </span>
                                    </td>
                                    <td className="p-4">
                                      <div className="flex flex-col gap-1">
                                        <span className="text-xs font-bold text-secondary uppercase tracking-wider">{c.domain?.replace('_', ' ') || 'Unknown'}</span>
                                        <span className="text-xs text-foreground/60">{c.highestDegree || 'None'}</span>
                                      </div>
                                    </td>
                                    <td className="p-4 max-w-xs">
                                      <div className="flex flex-wrap gap-1.5">
                                        {c.missing?.slice(0, 3).map((m, i) => (
                                          <span key={i} className="text-xs bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-md font-medium truncate max-w-[120px]">{m}</span>
                                        ))}
                                        {c.missing?.length > 3 && <span className="text-xs text-foreground/50 font-medium">+{c.missing.length - 3}</span>}
                                        {(!c.missing || c.missing.length === 0) && <span className="text-xs text-green-400 bg-green-500/10 px-2 py-0.5 rounded-md">None</span>}
                                      </div>
                                    </td>
                                    <td className="p-4 pr-6 text-right">
                                      <div className="flex items-center justify-end gap-3">
                                        <button 
                                          className="text-secondary hover:text-foreground text-sm font-bold flex items-center group"
                                          onClick={(e) => { e.stopPropagation(); setSelectedCandidate(c); }}
                                        >
                                          View Details <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                                        </button>
                                        <button
                                          onClick={(e) => handleDeleteCandidate(e, c.id)}
                                          className="text-foreground/50 hover:text-red-500 p-1.5 rounded-md hover:bg-red-500/10 transition-colors"
                                          title="Delete candidate"
                                        >
                                          <Trash2 className="w-4 h-4" />
                                        </button>
                                      </div>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div className="flex-1 overflow-x-auto p-6 bg-black/5 dark:bg-black/10">
                            <div className="flex gap-6 min-w-max h-full">
                              {['new', 'shortlisted', 'interviewing', 'hired', 'rejected'].map(statusCol => (
                                <div 
                                  key={statusCol}
                                  className="w-80 flex flex-col bg-surface border border-border rounded-2xl overflow-hidden shadow-lg"
                                  onDragOver={handleDragOver}
                                  onDrop={(e) => handleDrop(e, statusCol)}
                                >
                                  <div className="p-4 border-b border-border bg-black/5 dark:bg-black/20 flex justify-between items-center">
                                    <h4 className="font-bold text-sm uppercase tracking-wider text-foreground/80">{statusCol}</h4>
                                    <span className="bg-secondary/20 text-secondary text-xs font-black px-2 py-0.5 rounded-full">
                                      {jobCandidates.filter(c => c.status === statusCol).length}
                                    </span>
                                  </div>
                                  <div className="flex-1 p-3 space-y-3 overflow-y-auto custom-scrollbar min-h-[150px]">
                                    {jobCandidates.filter(c => c.status === statusCol).map(c => (
                                      <div 
                                        key={c.id} 
                                        draggable
                                        onDragStart={(e) => handleDragStart(e, c.id)}
                                        onClick={() => setSelectedCandidate(c)}
                                        className="bg-background border border-border rounded-xl p-4 cursor-grab active:cursor-grabbing hover:border-secondary/50 transition-all shadow-sm"
                                      >
                                        <div className="flex justify-between items-start mb-2">
                                          <h5 className="font-bold text-foreground text-sm truncate pr-2">{c.name}</h5>
                                          <div className={`text-xs font-black px-2 py-0.5 rounded border ${getScoreColor(c.score)}`}>{c.score}%</div>
                                        </div>
                                        <p className="text-xs text-foreground/60 truncate mb-3">{c.email}</p>
                                        <div className="flex gap-2">
                                          <span className="text-[10px] bg-surface border border-border px-2 py-1 rounded text-foreground/70">{c.experienceYears} YOE</span>
                                          {c.missing.length > 0 && <span className="text-[10px] bg-red-500/10 border border-red-500/20 px-2 py-1 rounded text-red-400">{c.missing.length} missing</span>}
                                        </div>
                                      </div>
                                    ))}
                                    {jobCandidates.filter(c => c.status === statusCol).length === 0 && (
                                      <div className="h-full flex items-center justify-center text-xs font-semibold text-foreground/30 uppercase tracking-widest border-2 border-dashed border-border rounded-xl p-8">
                                        Drop Here
                                      </div>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      ) : (
                        <div className="p-12 text-center flex flex-col items-center">
                          <Users className="w-12 h-12 text-foreground/40 mb-4" />
                          <p className="text-foreground/60 font-medium">No candidates processed yet for this job.</p>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center p-20 text-center border border-dashed border-border rounded-3xl bg-surface backdrop-blur-md">
                    <div className="w-24 h-24 bg-surface hover:bg-surface-hover rounded-full flex items-center justify-center mb-6 border border-border">
                      <Briefcase className="w-10 h-10 text-foreground/50" />
                    </div>
                    <h2 className="text-2xl font-bold text-foreground mb-3">No Active Job</h2>
                    <p className="text-foreground/60 max-w-md">Select a job from the sidebar or create a new one to start analyzing candidates.</p>
                  </div>
                )}
              </div>
            ) : (
              /* PROFILE TAB */
              <div className="max-w-2xl animate-fade-in">
                <div className="bg-surface border border-border p-10 rounded-3xl backdrop-blur-xl shadow-2xl relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-secondary to-purple-500"></div>
                  <header className="border-b border-border pb-8 mb-8 flex items-center space-x-5">
                    <div className="p-4 bg-secondary/10 rounded-2xl border border-secondary/20">
                      <Building2 className="w-8 h-8 text-secondary" />
                    </div>
                    <div>
                      <h2 className="text-3xl font-extrabold text-foreground">Company Profile</h2>
                      <p className="text-foreground/60 mt-1">Manage your recruiter details.</p>
                    </div>
                  </header>
                  <form onSubmit={handleSaveProfile} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-bold text-foreground/80 mb-2">Recruiter Name</label>
                        <input type="text" value={profile.fullName} onChange={e => setProfile({ ...profile, fullName: e.target.value })} className="w-full bg-surface border-border border border-border rounded-xl p-4 text-foreground focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" />
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-foreground/80 mb-2">Company Name</label>
                        <input type="text" value={profile.companyName} onChange={e => setProfile({ ...profile, companyName: e.target.value })} className="w-full bg-surface border-border border border-border rounded-xl p-4 text-foreground focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-foreground/80 mb-2">Company Website</label>
                      <input type="url" value={profile.companyWebsite} onChange={e => setProfile({ ...profile, companyWebsite: e.target.value })} className="w-full bg-surface border-border border border-border rounded-xl p-4 text-foreground focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-all" />
                    </div>
                    <div className="pt-6 border-t border-border flex justify-end">
                      <button type="submit" disabled={saveLoading} className="bg-secondary hover:bg-purple-600 disabled:bg-gray-800 text-white px-8 py-3.5 rounded-xl font-bold transition-all shadow-lg flex items-center">
                        {saveLoading && <Loader2 className="w-5 h-5 animate-spin mr-2" />}
                        {saveLoading ? 'Saving...' : 'Save Profile'}
                      </button>
                    </div>
                  </form>

                  {/* 2FA SETUP COMPONENT */}
                  <div className="pt-8 border-t border-border mt-8">
                    <TwoFactorSetup isEnabled={profile.twoFactorEnabled} method={profile.twoFactorMethod} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* CANDIDATE SLIDE-OUT PANEL */}
        {selectedCandidate && (
          <div className="absolute right-0 top-0 bottom-0 w-full lg:w-[30rem] bg-[#0a0a0f] border-l border-border shadow-[-20px_0_40px_rgba(0,0,0,0.5)] z-50 lg:z-40 flex flex-col animate-slide-in-right">
            <div className="flex items-center justify-between p-6 border-b border-border bg-surface hover:bg-surface-hover shrink-0">
              <h3 className="text-xl font-bold text-foreground">Candidate Analysis</h3>
              <button onClick={() => setSelectedCandidate(null)} className="p-2 text-foreground/60 hover:text-foreground bg-black/5 dark:bg-black/20 hover:bg-surface-hover rounded-full transition-colors border border-border">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
              {/* Top Banner */}
              <div className="text-center">
                <div className="w-20 h-20 mx-auto rounded-full bg-secondary/10 border border-secondary/20 flex items-center justify-center mb-4 shadow-lg shadow-secondary/10">
                  <User className="w-10 h-10 text-secondary" />
                </div>
                <h2 className="text-2xl font-black text-foreground">{selectedCandidate.name}</h2>
                <p className="text-foreground/60 mt-1">{selectedCandidate.email}</p>
                <div className="mt-4 flex justify-center">
                   <div className={`px-6 py-2 rounded-xl border flex flex-col items-center ${getScoreColor(selectedCandidate.score)}`}>
                     <span className="text-xs uppercase tracking-widest font-bold opacity-80 mb-0.5">ATS Score</span>
                     <span className="text-4xl font-black">{selectedCandidate.score}%</span>
                   </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface hover:bg-surface-hover border border-border p-3 rounded-xl">
                  <p className="text-[10px] text-foreground/50 font-bold uppercase mb-1">Domain</p>
                  <p className="text-sm font-semibold capitalize text-foreground">{selectedCandidate.domain?.replace('_', ' ') || 'Unknown'}</p>
                </div>
                <div className="bg-surface hover:bg-surface-hover border border-border p-3 rounded-xl">
                  <p className="text-[10px] text-foreground/50 font-bold uppercase mb-1">Experience</p>
                  <p className="text-sm font-semibold text-foreground">{selectedCandidate.experienceYears || 0} Years</p>
                </div>
              </div>

              {/* Skills */}
              <div className="space-y-6">
                <div>
                  <h4 className="text-sm font-bold text-foreground flex items-center mb-3">
                    <XCircle className="w-4 h-4 text-red-400 mr-2" /> Missing Core Skills ({selectedCandidate.missing?.length || 0})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedCandidate.missing?.map((m, i) => (
                      <span key={i} className="text-xs bg-red-500/10 border border-red-500/20 text-red-400 px-2.5 py-1 rounded-md">{m}</span>
                    ))}
                    {(!selectedCandidate.missing || selectedCandidate.missing.length === 0) && (
                      <span className="text-xs text-foreground/50 italic">No missing skills detected.</span>
                    )}
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-bold text-foreground flex items-center mb-3">
                    <CheckCircle2 className="w-4 h-4 text-green-400 mr-2" /> Matched Skills ({selectedCandidate.matched?.length || 0})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedCandidate.matched?.map((m, i) => (
                      <span key={i} className="text-xs bg-green-500/10 border border-green-500/20 text-green-400 px-2.5 py-1 rounded-md">{m}</span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Formatting & Structure */}
              {selectedCandidate.formatting && (
                <div className="border-t border-border pt-6">
                  <h4 className="text-sm font-bold text-foreground flex items-center mb-4">
                    <BarChart className="w-4 h-4 text-purple-400 mr-2" /> Resume Quality
                  </h4>
                  
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-black/30 border border-border p-3 rounded-xl">
                      <p className="text-[10px] text-foreground/50 font-bold uppercase mb-1">Action Verbs</p>
                      <p className={`text-base font-bold ${selectedCandidate.formatting.action_verb_rate > 50 ? 'text-green-400' : 'text-red-400'}`}>
                        {(selectedCandidate.formatting.action_verb_rate).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-black/30 border border-border p-3 rounded-xl">
                      <p className="text-[10px] text-foreground/50 font-bold uppercase mb-1">Quantified Metrics</p>
                      <p className={`text-base font-bold ${selectedCandidate.formatting.quantification_rate > 20 ? 'text-green-400' : 'text-red-400'}`}>
                        {(selectedCandidate.formatting.quantification_rate).toFixed(0)}%
                      </p>
                    </div>
                  </div>

                  {selectedCandidate.formatting.ats_warnings?.length > 0 && (
                    <div className="space-y-2 mt-3">
                      {selectedCandidate.formatting.ats_warnings.map((warn: string, i: number) => (
                        <div key={i} className="flex items-start bg-orange-500/10 border border-orange-500/20 p-3 rounded-lg">
                          <FileWarning className="w-4 h-4 text-orange-400 mr-2 mt-0.5 shrink-0" />
                          <p className="text-xs text-orange-200">{warn}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* LLM Feedback */}
              {(selectedCandidate.tips?.length ?? 0) > 0 && (
                <div className="border-t border-border pt-6">
                   <h4 className="text-sm font-bold text-foreground flex items-center mb-4">
                    <Zap className="w-4 h-4 text-yellow-400 mr-2" /> AI Summary & Tips
                  </h4>
                  <div className="space-y-3">
                    {selectedCandidate.tips?.map((tip: any, i: number) => (
                      <div key={i} className="bg-surface hover:bg-surface-hover border border-border p-4 rounded-xl">
                        <p className="text-xs text-foreground/80"><strong className="text-foreground">Issue:</strong> {tip.issue_found}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-6 border-t border-border bg-surface border-border shrink-0">
              <a 
                href={selectedCandidate.resumeUrl || "#"} 
                target="_blank"
                className="w-full bg-surface-hover hover:bg-white/20 text-foreground px-4 py-3 rounded-xl font-bold flex items-center justify-center transition-colors border border-border"
              >
                <FileText className="w-4 h-4 mr-2" /> View Original Resume
              </a>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
