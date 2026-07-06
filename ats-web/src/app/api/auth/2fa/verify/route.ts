import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth/next'
import { authOptions } from '@/lib/auth'
import { query } from '@/lib/db'
import speakeasy from 'speakeasy'
export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions)
    if (!session?.user?.email) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { token } = await req.json()
    if (!token) {
      return NextResponse.json({ error: 'Missing 2FA token' }, { status: 400 })
    }

    const email = session.user.email

    // Get the user's secret
    const { rows } = await query('SELECT totp_secret FROM users WHERE email = $1', [email])
    if (rows.length === 0 || !rows[0].totp_secret) {
      return NextResponse.json({ error: '2FA setup not initiated' }, { status: 400 })
    }

    const secret = rows[0].totp_secret

    // Verify the token
    const isValid = speakeasy.totp.verify({ secret, encoding: 'base32', token, window: 1 })

    if (isValid) {
      // Enable 2FA
      await query(`
        UPDATE users 
        SET two_factor_enabled = true 
        WHERE email = $1
      `, [email])
      
      return NextResponse.json({ success: true })
    } else {
      return NextResponse.json({ error: 'Invalid 2FA token' }, { status: 400 })
    }

  } catch (error) {
    console.error('Error verifying 2FA:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}
