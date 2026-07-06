'use client'

import { useState, Suspense } from 'react'
import { Lock, ArrowRight, AlertCircle, CheckCircle2, XCircle } from 'lucide-react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'

function ResetPasswordForm() {
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')
  
  const searchParams = useSearchParams()
  const token = searchParams.get('token')
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setStatus('idle')
    setMessage('')

    if (password !== confirmPassword) {
      setStatus('error')
      setMessage('Passwords do not match')
      setLoading(false)
      return
    }

    if (!token) {
      setStatus('error')
      setMessage('Invalid or missing reset token')
      setLoading(false)
      return
    }

    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, newPassword: password })
      })
      const data = await res.json()

      if (res.ok) {
        setStatus('success')
        setMessage('Your password has been successfully reset.')
        setTimeout(() => {
          router.push('/login')
        }, 3000)
      } else {
        setStatus('error')
        setMessage(data.error || 'Failed to reset password')
      }
    } catch (err) {
      setStatus('error')
      setMessage('Network error. Please try again.')
    }
    setLoading(false)
  }

  if (status === 'success') {
    return (
      <div className="text-center space-y-6 animate-in zoom-in fade-in duration-300">
        <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto border border-green-500/30">
          <CheckCircle2 className="w-8 h-8 text-green-400" />
        </div>
        <p className="text-gray-300">{message}</p>
        <p className="text-sm text-gray-500">Redirecting to login...</p>
      </div>
    )
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="relative">
        <Lock className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
        <input 
          type="password" 
          placeholder="New Password" 
          required 
          value={password}
          onChange={e => setPassword(e.target.value)} 
          className="w-full pl-10 pr-4 py-3 bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white transition-colors" 
        />
      </div>

      <div className="relative">
        <Lock className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
        <input 
          type="password" 
          placeholder="Confirm New Password" 
          required 
          value={confirmPassword}
          onChange={e => setConfirmPassword(e.target.value)} 
          className="w-full pl-10 pr-4 py-3 bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white transition-colors" 
        />
      </div>

      {/* Password Strength Indicator */}
      {password.length > 0 && (
        <div className="bg-black/30 p-4 rounded-lg border border-white/5 space-y-2 text-sm animate-in fade-in duration-200">
          <p className="text-gray-400 font-semibold mb-2">Password Requirements:</p>
          <div className="grid grid-cols-2 gap-2">
            <div className={`flex items-center ${password.length >= 12 ? 'text-green-400' : 'text-gray-500'}`}>
              {password.length >= 12 ? <CheckCircle2 className="w-4 h-4 mr-2 shrink-0" /> : <XCircle className="w-4 h-4 mr-2 shrink-0" />}
              <span>12+ characters</span>
            </div>
            <div className={`flex items-center ${/[A-Z]/.test(password) ? 'text-green-400' : 'text-gray-500'}`}>
              {/[A-Z]/.test(password) ? <CheckCircle2 className="w-4 h-4 mr-2 shrink-0" /> : <XCircle className="w-4 h-4 mr-2 shrink-0" />}
              <span>Uppercase letter</span>
            </div>
            <div className={`flex items-center ${/[a-z]/.test(password) ? 'text-green-400' : 'text-gray-500'}`}>
              {/[a-z]/.test(password) ? <CheckCircle2 className="w-4 h-4 mr-2 shrink-0" /> : <XCircle className="w-4 h-4 mr-2 shrink-0" />}
              <span>Lowercase letter</span>
            </div>
            <div className={`flex items-center ${/[0-9]/.test(password) ? 'text-green-400' : 'text-gray-500'}`}>
              {/[0-9]/.test(password) ? <CheckCircle2 className="w-4 h-4 mr-2 shrink-0" /> : <XCircle className="w-4 h-4 mr-2 shrink-0" />}
              <span>Number</span>
            </div>
            <div className={`flex items-center ${/[!@#$%^&*(),.?":{}|<>]/.test(password) ? 'text-green-400' : 'text-gray-500'}`}>
              {/[!@#$%^&*(),.?":{}|<>]/.test(password) ? <CheckCircle2 className="w-4 h-4 mr-2 shrink-0" /> : <XCircle className="w-4 h-4 mr-2 shrink-0" />}
              <span>Special character</span>
            </div>
            <div className={`flex items-center ${password === confirmPassword && confirmPassword.length > 0 ? 'text-green-400' : 'text-gray-500'}`}>
              {password === confirmPassword && confirmPassword.length > 0 ? <CheckCircle2 className="w-4 h-4 mr-2 shrink-0" /> : <XCircle className="w-4 h-4 mr-2 shrink-0" />}
              <span>Passwords match</span>
            </div>
          </div>
        </div>
      )}
      
      <div className="pt-2">
        <button 
          type="submit"
          disabled={loading || password !== confirmPassword || password.length < 12}
          className={`w-full text-white py-3 rounded-lg font-semibold transition-all flex justify-center items-center group shadow-lg ${
            (loading || password !== confirmPassword || password.length < 12) ? 'bg-gray-600 cursor-not-allowed' : 'bg-primary hover:bg-blue-600 shadow-blue-500/20'
          }`}
        >
          {loading ? 'Resetting...' : 'Reset Password'}
          {!loading && <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />}
        </button>
      </div>

      <div className="text-center pt-4">
        <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
          Cancel and return to Login
        </Link>
      </div>
    </form>
  )
}

export default function ResetPassword() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-primary/20 rounded-full blur-[100px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-secondary/20 rounded-full blur-[100px]" />

      <div className="z-10 w-full max-w-md p-8 bg-surface border border-white/10 backdrop-blur-xl rounded-2xl shadow-2xl">
        <h2 className="text-3xl font-bold text-center mb-2 text-white">Create New Password</h2>
        <p className="text-center text-gray-400 mb-6">Your new password must be at least 12 characters and highly secure.</p>

        <Suspense fallback={<div className="text-center text-gray-500 py-10">Loading securely...</div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  )
}
