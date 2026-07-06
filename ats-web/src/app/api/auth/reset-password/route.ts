import { NextResponse } from 'next/server'
import { query } from '@/lib/db'
import bcrypt from 'bcrypt'

export async function POST(req: Request) {
  try {
    const { token, newPassword } = await req.json()

    if (!token || !newPassword) {
      return NextResponse.json({ error: 'Token and new password are required' }, { status: 400 })
    }

    // Server-side validation
    if (newPassword.length < 12 || !/[A-Z]/.test(newPassword) || !/[a-z]/.test(newPassword) || !/[0-9]/.test(newPassword) || !/[!@#$%^&*(),.?":{}|<>]/.test(newPassword)) {
      return NextResponse.json({ error: 'Password does not meet complexity requirements' }, { status: 400 })
    }

    // Find valid token
    const { rows } = await query(
      `SELECT id, email FROM users 
       WHERE reset_token = $1 AND reset_token_expires > now()`,
      [token]
    )

    if (rows.length === 0) {
      return NextResponse.json({ error: 'Invalid or expired reset token' }, { status: 400 })
    }

    const user = rows[0]
    
    // Hash new password
    const saltRounds = 10
    const salt = await bcrypt.genSalt(saltRounds)
    const passwordHash = await bcrypt.hash(newPassword, salt)

    // Update password and clear token
    await query(
      `UPDATE users 
       SET password_hash = $1, salt = $2, reset_token = NULL, reset_token_expires = NULL 
       WHERE id = $3`,
      [passwordHash, salt, user.id]
    )

    return NextResponse.json({ success: true, message: 'Password reset successfully' })

  } catch (error: any) {
    console.error('Reset password error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
