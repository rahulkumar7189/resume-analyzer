import { NextResponse } from 'next/server'
import { query } from '@/lib/db'
import crypto from 'crypto'

export async function POST(req: Request) {
  try {
    const { email } = await req.json()
    if (!email) return NextResponse.json({ error: 'Email is required' }, { status: 400 })

    // Generate secure token
    const token = crypto.randomBytes(32).toString('hex')
    const expires = new Date(Date.now() + 3600000) // 1 hour from now

    // Check if user exists and save token (we use a transaction-like update)
    const { rowCount } = await query(
      `UPDATE users 
       SET reset_token = $1, reset_token_expires = $2 
       WHERE email = $3`,
      [token, expires, email]
    )

    if (rowCount === 0) {
      // Return success anyway to prevent email enumeration attacks
      return NextResponse.json({ success: true, message: 'If an account exists, a reset link has been sent.' })
    }

    // In a real application, you would send an email here using Resend/SendGrid etc.
    // For local development, we will log it to the server console.
    const resetUrl = `${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/reset-password?token=${token}`
    console.log('\n=============================================================')
    console.log('🔒 PASSWORD RESET LINK GENERATED')
    console.log(`To reset the password for ${email}, go to:`)
    console.log(resetUrl)
    console.log('=============================================================\n')

    return NextResponse.json({ 
      success: true, 
      message: 'If an account exists, a reset link has been sent.',
      _devToken: process.env.NODE_ENV === 'development' ? token : undefined // Help dev testing
    })

  } catch (error: any) {
    console.error('Forgot password error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
