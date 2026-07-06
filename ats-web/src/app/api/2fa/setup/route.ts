import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { query } from '@/lib/db'
import speakeasy from 'speakeasy'
import QRCode from 'qrcode'
import { generateRegistrationOptions, verifyRegistrationResponse } from '@simplewebauthn/server'

const rpName = 'ATS Platform'
const rpID = 'localhost' // In production, this must match the domain
const origin = `http://${rpID}:3000`

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions)
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { action, payload } = await req.json()
    const userId = session.user.id
    const userEmail = session.user.email

    if (action === 'generate_totp') {
      const secretInfo = speakeasy.generateSecret({ name: 'ATS Platform (' + (userEmail || 'user') + ')' })
      const secret = secretInfo.base32
      const otpauth = secretInfo.otpauth_url || ''
      const qrCodeDataUrl = await QRCode.toDataURL(otpauth)

      // Store temporarily (ideally in a cache, but for now we update the user row with disabled state)
      await query(
        'UPDATE users SET totp_secret = $1 WHERE id = $2',
        [secret, userId]
      )

      return NextResponse.json({ secret, qrCodeDataUrl })
    }

    if (action === 'verify_totp') {
      const { code } = payload
      const { rows } = await query('SELECT totp_secret FROM users WHERE id = $1', [userId])
      const secret = rows[0]?.totp_secret

      if (!secret) {
        return NextResponse.json({ error: 'No TOTP secret found' }, { status: 400 })
      }

      const isValid = speakeasy.totp.verify({ secret, encoding: 'base32', token: code, window: 1 })
      
      if (isValid) {
        await query(
          "UPDATE users SET two_factor_enabled = true, two_factor_method = 'totp' WHERE id = $1",
          [userId]
        )
        return NextResponse.json({ success: true })
      } else {
        return NextResponse.json({ error: 'Invalid code' }, { status: 400 })
      }
    }

    if (action === 'setup_sms') {
      const { phone } = payload
      const otp = Math.floor(100000 + Math.random() * 900000).toString()
      
      // Store phone and temporary code in DB (reusing totp_secret column as temporary storage for mock)
      await query(
        'UPDATE users SET phone_number = $1, totp_secret = $2 WHERE id = $3',
        [phone, otp, userId]
      )

      console.log(`\n\n=== MOCK SMS TO ${phone} ===`)
      console.log(`Your ATS 2FA code is: ${otp}`)
      console.log(`============================\n\n`)

      return NextResponse.json({ success: true })
    }

    if (action === 'verify_sms') {
      const { code } = payload
      const { rows } = await query('SELECT totp_secret FROM users WHERE id = $1', [userId])
      const expectedCode = rows[0]?.totp_secret

      if (code === expectedCode) {
        await query(
          "UPDATE users SET two_factor_enabled = true, two_factor_method = 'sms', totp_secret = NULL WHERE id = $1",
          [userId]
        )
        return NextResponse.json({ success: true })
      } else {
        return NextResponse.json({ error: 'Invalid SMS code' }, { status: 400 })
      }
    }

    if (action === 'disable_2fa') {
      await query(
        "UPDATE users SET two_factor_enabled = false, two_factor_method = NULL, totp_secret = NULL, webauthn_credential_id = NULL, webauthn_public_key = NULL WHERE id = $1",
        [userId]
      )
      return NextResponse.json({ success: true })
    }

    if (action === 'generate_webauthn_options') {
      const options = await generateRegistrationOptions({
        rpName,
        rpID,
        userID: new Uint8Array(Buffer.from(String(userId))),
        userName: userEmail || 'user',
        attestationType: 'none',
        authenticatorSelection: {
          residentKey: 'preferred',
          userVerification: 'preferred',
        },
      })
      // Save challenge temporarily
      await query('UPDATE users SET totp_secret = $1 WHERE id = $2', [options.challenge, userId])
      return NextResponse.json(options)
    }

    if (action === 'verify_webauthn_registration') {
      const { rows } = await query('SELECT totp_secret FROM users WHERE id = $1', [userId])
      const expectedChallenge = rows[0]?.totp_secret

      let verification
      try {
        verification = await verifyRegistrationResponse({
          response: payload,
          expectedChallenge,
          expectedOrigin: origin,
          expectedRPID: rpID,
        })
      } catch (err: any) {
        return NextResponse.json({ error: err.message }, { status: 400 })
      }

      const { verified, registrationInfo } = verification
      if (verified && registrationInfo) {
        const { credential } = registrationInfo
        
        // Save credential
        const credIdBase64 = credential.id
        const pubKeyBase64 = Buffer.from(credential.publicKey).toString('base64')

        await query(
          "UPDATE users SET two_factor_enabled = true, two_factor_method = 'webauthn', webauthn_credential_id = $1, webauthn_public_key = $2, totp_secret = NULL WHERE id = $3",
          [credIdBase64, pubKeyBase64, userId]
        )
        return NextResponse.json({ success: true })
      }
      return NextResponse.json({ error: 'Verification failed' }, { status: 400 })
    }

    return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
  } catch (error) {
    console.error('2FA setup error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
