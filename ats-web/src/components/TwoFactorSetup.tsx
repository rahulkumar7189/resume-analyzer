'use client'

import { useState } from 'react'
import { Shield, Smartphone, Key, X, Check } from 'lucide-react'
import { useToast } from '@/components/ui/ToastProvider'

export default function TwoFactorSetup({ isEnabled, method }: { isEnabled: boolean, method: string | null }) {
  const [activeTab, setActiveTab] = useState<'totp' | 'sms' | 'webauthn'>('totp')
  const [qrCode, setQrCode] = useState('')
  const [secret, setSecret] = useState('')
  const [code, setCode] = useState('')
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)
  const { addToast } = useToast()

  const handleGenerateTotp = async () => {
    setLoading(true)
    const res = await fetch('/api/2fa/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'generate_totp' })
    })
    const data = await res.json()
    if (data.qrCodeDataUrl) {
      setQrCode(data.qrCodeDataUrl)
      setSecret(data.secret)
    }
    setLoading(false)
  }

  const handleVerifyTotp = async () => {
    setLoading(true)
    const res = await fetch('/api/2fa/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'verify_totp', payload: { code } })
    })
    if (res.ok) {
      addToast('Authenticator App linked successfully!', 'success')
      window.location.reload()
    } else {
      addToast('Invalid verification code.', 'error')
    }
    setLoading(false)
  }

  const handleSetupSms = async () => {
    setLoading(true)
    await fetch('/api/2fa/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'setup_sms', payload: { phone } })
    })
    addToast('SMS sent to your phone!', 'success')
    setLoading(false)
  }

  const handleVerifySms = async () => {
    setLoading(true)
    const res = await fetch('/api/2fa/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'verify_sms', payload: { code } })
    })
    if (res.ok) {
      addToast('Phone number verified and linked!', 'success')
      window.location.reload()
    } else {
      addToast('Invalid SMS code.', 'error')
    }
    setLoading(false)
  }

  const handleDisable = async () => {
    await fetch('/api/2fa/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'disable_2fa' })
    })
    addToast('Two-Factor Authentication disabled.', 'info')
    window.location.reload()
  }

  if (isEnabled) {
    return (
      <div className="bg-black/30 border border-white/10 rounded-xl p-6 mt-6 max-w-2xl text-white">
        <h3 className="text-xl font-bold flex items-center mb-4 text-green-400">
          <Shield className="w-6 h-6 mr-2" />
          Two-Factor Authentication Enabled
        </h3>
        <p className="text-gray-400 mb-6">Your account is secured using <strong className="text-white uppercase">{method}</strong>.</p>
        <button 
          onClick={handleDisable}
          className="px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/40 rounded-lg transition-colors flex items-center font-semibold"
        >
          <X className="w-4 h-4 mr-2" /> Disable 2FA
        </button>
      </div>
    )
  }

  return (
    <div className="bg-black/30 border border-white/10 rounded-xl p-6 mt-6 max-w-2xl text-white">
      <h3 className="text-xl font-bold flex items-center mb-4">
        <Shield className="w-6 h-6 mr-2" />
        Set Up Two-Factor Authentication
      </h3>
      <p className="text-gray-400 mb-6">Add an extra layer of security to your account. Choose a method below.</p>

      <div className="flex space-x-2 mb-6">
        <button 
          onClick={() => setActiveTab('totp')}
          className={`flex-1 py-2 px-4 rounded-lg flex items-center justify-center transition-colors ${activeTab === 'totp' ? 'bg-primary shadow-lg shadow-primary/20 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
        >
          <Shield className="w-4 h-4 mr-2" /> Authenticator App
        </button>
        <button 
          onClick={() => setActiveTab('sms')}
          className={`flex-1 py-2 px-4 rounded-lg flex items-center justify-center transition-colors ${activeTab === 'sms' ? 'bg-primary shadow-lg shadow-primary/20 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
        >
          <Smartphone className="w-4 h-4 mr-2" /> Text Message (SMS)
        </button>
      </div>

      {activeTab === 'totp' && (
        <div className="space-y-4 animate-in fade-in">
          {!qrCode ? (
            <div>
              <p className="text-sm text-gray-400 mb-4">Use an app like Google Authenticator or Authy to scan a QR code.</p>
              <button 
                onClick={handleGenerateTotp}
                disabled={loading}
                className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors font-semibold"
              >
                {loading ? 'Generating...' : 'Generate QR Code'}
              </button>
            </div>
          ) : (
            <div className="flex flex-col md:flex-row gap-6 items-start">
              <div className="bg-white p-2 rounded-lg">
                <img src={qrCode} alt="QR Code" className="w-48 h-48" />
              </div>
              <div className="flex-1 space-y-4">
                <p className="text-sm text-gray-400">1. Scan the QR code with your Authenticator app.</p>
                <p className="text-sm text-gray-400">2. Enter the 6-digit code generated by the app.</p>
                <div className="flex space-x-2">
                  <input 
                    type="text" 
                    placeholder="000000"
                    maxLength={6}
                    value={code}
                    onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
                    className="w-32 text-center text-xl tracking-widest pl-4 pr-4 py-2 bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white" 
                  />
                  <button 
                    onClick={handleVerifyTotp}
                    disabled={loading || code.length !== 6}
                    className="px-6 py-2 bg-primary hover:bg-blue-600 rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Verify & Enable
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'sms' && (
        <div className="space-y-4 animate-in fade-in">
          <p className="text-sm text-gray-400 mb-4">We will send a text message with a verification code to your phone.</p>
          <div className="flex space-x-2 mb-4">
            <input 
              type="text" 
              placeholder="+1 (555) 000-0000"
              value={phone}
              onChange={e => setPhone(e.target.value)}
              className="flex-1 px-4 py-2 bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white" 
            />
            <button 
              onClick={handleSetupSms}
              disabled={loading || phone.length < 5}
              className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors font-semibold"
            >
              Send Code
            </button>
          </div>

          <div className="flex space-x-2 border-t border-white/10 pt-4 mt-4">
            <input 
              type="text" 
              placeholder="000000"
              maxLength={6}
              value={code}
              onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
              className="w-32 text-center text-xl tracking-widest pl-4 pr-4 py-2 bg-black/50 border border-white/10 rounded-lg focus:outline-none focus:border-primary text-white" 
            />
            <button 
              onClick={handleVerifySms}
              disabled={loading || code.length !== 6}
              className="px-6 py-2 bg-primary hover:bg-blue-600 rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Verify & Enable
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
