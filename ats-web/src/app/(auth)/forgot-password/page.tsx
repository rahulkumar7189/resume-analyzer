'use client'

import { useState } from 'react'
import { Mail, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react'
import Link from 'next/link'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setStatus('idle')
    setMessage('')

    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      })
      const data = await res.json()

      if (res.ok) {
        setStatus('success')
        setMessage(data.message || 'If an account exists, a reset link has been sent.')
      } else {
        setStatus('error')
        setMessage(data.error || 'Failed to request reset')
      }
    } catch (err) {
      setStatus('error')
      setMessage('Network error. Please try again.')
    }
    setLoading(false)
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-primary/20 rounded-full blur-[100px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-secondary/20 rounded-full blur-[100px]" />

      <div className="z-10 w-full max-w-md p-8 bg-surface border border-white/10 backdrop-blur-xl rounded-2xl shadow-2xl">
        <h2 className="text-3xl font-bold text-center mb-2 text-white">Reset Password</h2>
        <p className="text-center text-gray-400 mb-6">Enter your email to receive a reset link</p>

        {status === 'error' && (
          <div className="mb-6 p-3 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center text-red-400 text-sm animate-in slide-in-from-top-2 fade-in">
            <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {status === 'success' ? (
          <div className="text-center space-y-6 animate-in zoom-in fade-in duration-300">
            <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto border border-green-500/30">
              <CheckCircle2 className="w-8 h-8 text-green-400" />
            </div>
            <p className="text-gray-300">{message}</p>
            <div className="pt-4">
              <Link href="/login" className="text-primary hover:text-white transition-colors font-semibold">
                Return to Login
              </Link>
            </div>
          </div>
        ) : (
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="relative">
              <Mail className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
              <input 
                type="email" 
                placeholder="Email address" 
                required 
                value={email}
                onChange={e => setEmail(e.target.value)} 
                className="w-full pl-10 pr-4 py-3 bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white transition-colors" 
              />
            </div>
            
            <div className="pt-2">
              <button 
                type="submit"
                disabled={loading}
                className={`w-full text-white py-3 rounded-lg font-semibold transition-all flex justify-center items-center group shadow-lg ${
                  loading ? 'bg-gray-600 cursor-not-allowed' : 'bg-primary hover:bg-blue-600 shadow-blue-500/20'
                }`}
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
                {!loading && <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />}
              </button>
            </div>

            <div className="text-center pt-4">
              <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
                Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
