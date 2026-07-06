import { NextResponse } from 'next/server'
import { query } from '@/lib/db'

export async function POST(req: Request) {
  try {
    const { email, otp } = await req.json()

    if (!email || !otp) {
      return NextResponse.json({ error: 'Missing email or OTP' }, { status: 400 })
    }

    // 1. Check if token exists and is valid
    const { rows: tokens } = await query(
      'SELECT * FROM verification_tokens WHERE email = $1',
      [email]
    )
    
    if (tokens.length === 0) {
      return NextResponse.json({ error: 'No pending registration found for this email' }, { status: 400 })
    }

    const tokenRecord = tokens[0]

    // 2. Check if expired
    if (new Date() > new Date(tokenRecord.expires_at)) {
      return NextResponse.json({ error: 'OTP has expired. Please sign up again.' }, { status: 400 })
    }

    // 3. Check if OTP matches
    if (tokenRecord.otp !== otp) {
      return NextResponse.json({ error: 'Invalid OTP code' }, { status: 400 })
    }

    // 4. Verification successful, insert into main users table
    const { rows: userRows } = await query(
      `INSERT INTO users (email, password_hash, salt, is_email_verified) 
       VALUES ($1, $2, $3, $4) RETURNING id`,
      [email, tokenRecord.pending_password_hash, tokenRecord.pending_salt, true]
    )
    
    const userId = userRows[0].id

    // 5. Insert profile
    await query(
      'INSERT INTO profiles (id, full_name, role) VALUES ($1, $2, $3)',
      [userId, tokenRecord.pending_full_name, tokenRecord.pending_role]
    )

    // 6. Delete the token so it can't be reused
    await query('DELETE FROM verification_tokens WHERE email = $1', [email])

    return NextResponse.json({ success: true })
  } catch (error: any) {
    if (error.code === '23505') {
      return NextResponse.json({ error: 'Email already exists' }, { status: 400 })
    }
    console.error('Email verification error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
