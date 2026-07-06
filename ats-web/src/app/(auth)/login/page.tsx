'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { User, Briefcase, Mail, Lock, ArrowRight, AlertCircle, CheckCircle2, XCircle } from 'lucide-react'
import { signIn } from 'next-auth/react'
import { useToast } from '@/components/ui/ToastProvider'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState<'candidate' | 'recruiter'>('candidate')
  const [isSignUp, setIsSignUp] = useState(false)
  const [show2fa, setShow2fa] = useState<{ required: boolean, method: string }>({ required: false, method: '' })
  const [twoFactorCode, setTwoFactorCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [authError, setAuthError] = useState('')
  const router = useRouter()
  const { addToast } = useToast()

  const handleAuth = async (e: React.FormEvent, type: 'login' | 'signup') => {
    e.preventDefault()
    setAuthError('')
    
    if (type === 'signup') {
      const hasLength = password.length >= 12
      const hasUpper = /[A-Z]/.test(password)
      const hasLower = /[a-z]/.test(password)
      const hasNumber = /[0-9]/.test(password)
      const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password)
      
      const emailPrefix = email.split('@')[0].toLowerCase()
      const isEmailUnique = emailPrefix.length <= 3 || !password.toLowerCase().includes(emailPrefix)
      const firstName = fullName.split(' ')[0].toLowerCase()
      const isNameUnique = firstName.length <= 3 || !password.toLowerCase().includes(firstName)

      if (!hasLength || !hasUpper || !hasLower || !hasNumber || !hasSpecial || !isEmailUnique || !isNameUnique) {
        setAuthError('Password does not meet the minimum security requirements.')
        setLoading(false)
        return
      }
    }

    setLoading(true)
    
    if (type === 'signup') {
      const res = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role, fullName })
      })
      const data = await res.json()
      
      if (!res.ok) {
        setAuthError(data.error || 'Failed to sign up')
      } else {
        // Fallback auto-login
        const result = await signIn('credentials', {
          redirect: false,
          email,
          password
        })
        if (result?.error) {
          setAuthError(result.error)
        } else {
          router.push(`/${role}`)
        }
      }
    } else {
      const result = await signIn('credentials', {
        redirect: false,
        email,
        password,
        role
      })
      if (result?.error) {
        if (result.error.startsWith('REQUIRES_2FA_')) {
          setShow2fa({ required: true, method: result.error.replace('REQUIRES_2FA_', '').toLowerCase() })
          addToast('Two-factor authentication required', 'info')
        } else if (result.error === 'CredentialsSignin') {
          setAuthError('Invalid credentials or role mismatch. Please check your email, password, and the selected tab.')
        } else {
          setAuthError(result.error)
        }
      } else {
        router.push(`/${role}`)
      }
    }
    setLoading(false)
  }

  const handleVerify2fa = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthError('')
    setLoading(true)
    
    // For webauthn, we'd normally call the navigator.credentials.get here.
    // For this stub, we just pass what the user types (if we were full WebAuthn, we'd trigger the browser prompt)
    const result = await signIn('credentials', {
      redirect: false,
      email,
      password,
      role,
      twoFactorCode: show2fa.method !== 'webauthn' ? twoFactorCode : undefined,
      webAuthnResponse: show2fa.method === 'webauthn' ? 'valid' : undefined // Mock for webauthn
    })

    if (result?.error) {
      setAuthError(result.error)
      setLoading(false)
    } else {
      addToast('Authentication successful!', 'success')
      router.push(`/${role}`)
    }
  }


  if (show2fa.required) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background relative overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-primary/20 rounded-full blur-[100px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-secondary/20 rounded-full blur-[100px]" />
  
        <div className="z-10 w-full max-w-md p-8 bg-surface border border-white/10 backdrop-blur-xl rounded-2xl shadow-2xl">
          <h2 className="text-3xl font-bold text-center mb-2 text-white">Two-Factor Auth</h2>
          <p className="text-center text-gray-400 mb-6">
            {show2fa.method === 'totp' && 'Enter the 6-digit code from your Authenticator app.'}
            {show2fa.method === 'sms' && 'Enter the 6-digit code sent to your phone via SMS.'}
            {show2fa.method === 'webauthn' && 'Use your Security Key or TouchID to verify.'}
          </p>
          
          {authError && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center text-red-400 text-sm animate-in slide-in-from-top-2 fade-in">
              <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
              <span>{authError}</span>
            </div>
          )}
          
          <form className="space-y-4" onSubmit={handleVerify2fa}>
            {show2fa.method !== 'webauthn' && (
              <div className="flex justify-center mb-6">
                <input 
                  type="text" 
                  maxLength={6}
                  placeholder="000000" 
                  required 
                  value={twoFactorCode}
                  onChange={e => setTwoFactorCode(e.target.value.replace(/\D/g, ''))} 
                  className="w-full text-center text-2xl tracking-widest pl-4 pr-4 py-3 bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white transition-colors" 
                />
              </div>
            )}
            
            <button 
              type="submit"
              disabled={loading || (show2fa.method !== 'webauthn' && twoFactorCode.length !== 6)}
              className={`w-full text-white py-3 rounded-lg font-semibold transition-all flex justify-center items-center group shadow-lg ${
                loading ? 'bg-gray-600 cursor-not-allowed' :
                role === 'candidate' ? 'bg-primary hover:bg-blue-600 shadow-blue-500/20' : 
                'bg-secondary hover:bg-purple-600 shadow-purple-500/20'
              }`}
            >
              {loading ? 'Verifying...' : (show2fa.method === 'webauthn' ? 'Tap Security Key' : 'Verify')}
            </button>
            
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setShow2fa({ required: false, method: '' })
                  setTwoFactorCode('')
                  setPassword('') // Force them to re-enter password if they cancel
                }}
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                Back to Login
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-primary/20 rounded-full blur-[100px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-secondary/20 rounded-full blur-[100px]" />

      <div className="z-10 w-full max-w-md p-8 bg-surface border border-white/10 backdrop-blur-xl rounded-2xl shadow-2xl">
        <h2 className="text-3xl font-bold text-center mb-2 text-white">
          {isSignUp ? 'Join ATS Platform' : 'Welcome Back'}
        </h2>
        <p className="text-center text-gray-400 mb-6">AI-Powered Resume Screening</p>
        
        {authError && (
          <div className="mb-6 p-3 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center text-red-400 text-sm animate-in slide-in-from-top-2 fade-in">
            <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
            <span>{authError}</span>
          </div>
        )}
        
        {/* Role Selector */}
        <div className="flex space-x-2 mb-6 bg-black/30 p-1 rounded-lg">
          <button
            onClick={() => setRole('candidate')}
            className={`flex-1 flex items-center justify-center py-2 rounded-md transition-all ${role === 'candidate' ? 'bg-primary text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
          >
            <User className="w-4 h-4 mr-2" />
            Candidate
          </button>
          <button
            onClick={() => setRole('recruiter')}
            className={`flex-1 flex items-center justify-center py-2 rounded-md transition-all ${role === 'recruiter' ? 'bg-secondary text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
          >
            <Briefcase className="w-4 h-4 mr-2" />
            Recruiter
          </button>
        </div>

        <form className="space-y-4" onSubmit={(e) => handleAuth(e, isSignUp ? 'signup' : 'login')}>
          {isSignUp && (
            <div className="relative animate-in slide-in-from-top-2 fade-in duration-200">
              <User className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
              <input 
                type="text" 
                placeholder="Full Name" 
                required 
                value={fullName}
                onChange={e => setFullName(e.target.value)} 
                className="w-full pl-10 pr-4 py-3 bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white transition-colors" 
              />
            </div>
          )}

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
          
          <div className="relative">
            <Lock className="absolute left-3 top-3 w-5 h-5 text-gray-500" />
            <input 
              type="password" 
              placeholder="Password" 
              required 
              value={password}
              onChange={e => setPassword(e.target.value)} 
              className="w-full pl-10 pr-4 py-3 bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white transition-colors" 
            />
          </div>

          {/* Password Strength Indicator */}
          {isSignUp && password.length > 0 && (
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
                <div className={`flex items-center ${(email.split('@')[0].length <= 3 || !password.toLowerCase().includes(email.split('@')[0].toLowerCase())) && (fullName.split(' ')[0].length <= 3 || !password.toLowerCase().includes(fullName.split(' ')[0].toLowerCase())) ? 'text-green-400' : 'text-gray-500'} col-span-2`}>
                  {((email.split('@')[0].length <= 3 || !password.toLowerCase().includes(email.split('@')[0].toLowerCase())) && (fullName.split(' ')[0].length <= 3 || !password.toLowerCase().includes(fullName.split(' ')[0].toLowerCase()))) ? <CheckCircle2 className="w-4 h-4 mr-2 shrink-0" /> : <XCircle className="w-4 h-4 mr-2 shrink-0" />}
                  <span>Must not contain name or email</span>
                </div>
              </div>
            </div>
          )}
          
          <div className="pt-2">
            <button 
              type="submit"
              disabled={loading}
              className={`w-full text-white py-3 rounded-lg font-semibold transition-all flex justify-center items-center group shadow-lg ${
                loading ? 'bg-gray-600 cursor-not-allowed' :
                role === 'candidate' ? 'bg-primary hover:bg-blue-600 shadow-blue-500/20' : 
                'bg-secondary hover:bg-purple-600 shadow-purple-500/20'
              }`}
            >
              {loading ? 'Processing...' : isSignUp ? 'Create Account' : 'Log In'}
              {!loading && <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />}
            </button>
          </div>

          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => setIsSignUp(!isSignUp)}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              {isSignUp ? 'Already have an account? Log In' : "Don't have an account? Sign Up"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
