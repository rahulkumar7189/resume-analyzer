'use client'

import { useState } from 'react'
import { Shield, Key, CheckCircle2, AlertCircle } from 'lucide-react'

export default function SecuritySettings() {
  const [loading, setLoading] = useState(false)
  const [qrCode, setQrCode] = useState<string | null>(null)
  const [totpSecret, setTotpSecret] = useState<string | null>(null)
  const [verificationCode, setVerificationCode] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [is2FAEnabled, setIs2FAEnabled] = useState(false) // Assuming we will fetch this from the user's profile on mount, but for now it's optimistic

  const handleSetup2FA = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/auth/2fa/setup', { method: 'POST' })
      const data = await res.json()
      
      if (res.ok) {
        setQrCode(data.qrCodeUrl)
        setTotpSecret(data.secret)
      } else {
        setError(data.error || 'Failed to setup 2FA')
      }
    } catch (err) {
      setError('An error occurred during setup.')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify2FA = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const res = await fetch('/api/auth/2fa/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: verificationCode })
      })
      const data = await res.json()
      
      if (res.ok) {
        setSuccess('Two-Factor Authentication has been successfully enabled!')
        setIs2FAEnabled(true)
        setQrCode(null)
      } else {
        setError(data.error || 'Invalid verification code')
      }
    } catch (err) {
      setError('An error occurred during verification.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Security Settings</h1>
        
        <div className="bg-surface border border-white/10 rounded-2xl p-8 mb-8 shadow-xl">
          <div className="flex items-center mb-6">
            <Shield className="w-8 h-8 text-primary mr-4" />
            <div>
              <h2 className="text-2xl font-semibold">Two-Factor Authentication (2FA)</h2>
              <p className="text-gray-400">Add an extra layer of security to your account.</p>
            </div>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center text-red-400">
              <AlertCircle className="w-5 h-5 mr-3 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 bg-green-500/10 border border-green-500/50 rounded-lg flex items-center text-green-400">
              <CheckCircle2 className="w-5 h-5 mr-3 shrink-0" />
              <span>{success}</span>
            </div>
          )}

          {!is2FAEnabled && !qrCode && (
            <div>
              <p className="mb-6 text-gray-300">
                Protect your account by requiring a 6-digit code from your authenticator app when you log in.
              </p>
              <button 
                onClick={handleSetup2FA} 
                disabled={loading}
                className="bg-primary hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold transition-all flex items-center shadow-lg shadow-blue-500/20 disabled:opacity-50"
              >
                <Key className="w-5 h-5 mr-2" />
                {loading ? 'Setting up...' : 'Setup Authenticator App'}
              </button>
            </div>
          )}

          {qrCode && !is2FAEnabled && (
            <div className="animate-in fade-in duration-300">
              <div className="bg-black/30 p-6 rounded-xl border border-white/5 mb-6">
                <h3 className="text-xl font-semibold mb-4">1. Scan the QR Code</h3>
                <p className="text-gray-400 mb-6">Open your authenticator app (like Google Authenticator or Authy) and scan the QR code below.</p>
                <div className="flex justify-center mb-6">
                  <div className="p-4 bg-white rounded-xl">
                    <img src={qrCode} alt="2FA QR Code" className="w-48 h-48" />
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-400 mb-2">Can't scan the code? Enter this secret manually:</p>
                  <code className="bg-black/50 px-4 py-2 rounded-lg text-primary tracking-widest">{totpSecret}</code>
                </div>
              </div>

              <div className="bg-black/30 p-6 rounded-xl border border-white/5">
                <h3 className="text-xl font-semibold mb-4">2. Verify the Code</h3>
                <p className="text-gray-400 mb-4">Enter the 6-digit code generated by your authenticator app to complete setup.</p>
                <form onSubmit={handleVerify2FA} className="flex gap-4">
                  <input 
                    type="text" 
                    maxLength={6}
                    placeholder="000000" 
                    value={verificationCode}
                    onChange={e => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                    className="flex-1 text-center text-2xl tracking-widest bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white transition-colors"
                    required
                  />
                  <button 
                    type="submit" 
                    disabled={loading || verificationCode.length !== 6}
                    className="bg-primary hover:bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Verifying...' : 'Verify'}
                  </button>
                </form>
              </div>
            </div>
          )}

          {is2FAEnabled && (
            <div className="p-6 bg-black/30 rounded-xl border border-white/5 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-green-400 flex items-center">
                  <CheckCircle2 className="w-5 h-5 mr-2" />
                  Authenticator App Enabled
                </h3>
                <p className="text-gray-400 text-sm mt-1">Your account is protected by 2FA.</p>
              </div>
              <button 
                className="px-4 py-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg font-semibold transition-colors border border-red-500/20"
                onClick={() => {
                  // Stub for disabling 2FA
                  alert('Disabling 2FA requires confirming your password. (Not implemented in this stub)')
                }}
              >
                Disable 2FA
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
