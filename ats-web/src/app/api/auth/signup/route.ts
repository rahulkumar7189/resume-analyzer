import { NextResponse } from 'next/server'
import { query } from '@/lib/db'
import bcrypt from 'bcrypt'

export async function POST(req: Request) {
  try {
    const { email, password, role, fullName } = await req.json()

    if (!email || !password || !role) {
      return NextResponse.json({ error: 'Missing fields' }, { status: 400 })
    }

    if (password.length < 12) {
      return NextResponse.json({ error: 'Password must be at least 12 characters long' }, { status: 400 })
    }
    if (!/[A-Z]/.test(password)) {
      return NextResponse.json({ error: 'Password must contain at least one uppercase letter' }, { status: 400 })
    }
    if (!/[a-z]/.test(password)) {
      return NextResponse.json({ error: 'Password must contain at least one lowercase letter' }, { status: 400 })
    }
    if (!/[0-9]/.test(password)) {
      return NextResponse.json({ error: 'Password must contain at least one number' }, { status: 400 })
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return NextResponse.json({ error: 'Password must contain at least one special character' }, { status: 400 })
    }
    
    // Uniqueness: Ensure password doesn't contain email prefix or first name
    const emailPrefix = email.split('@')[0].toLowerCase()
    if (emailPrefix.length > 3 && password.toLowerCase().includes(emailPrefix)) {
      return NextResponse.json({ error: 'Password must be unique and cannot contain your email' }, { status: 400 })
    }
    if (fullName) {
      const firstName = fullName.split(' ')[0].toLowerCase()
      if (firstName.length > 3 && password.toLowerCase().includes(firstName)) {
        return NextResponse.json({ error: 'Password must be unique and cannot contain your name' }, { status: 400 })
      }
    }

    // First, check if the email is already in the main users table
    const { rows: existingUsers } = await query(
      `SELECT u.id, p.role 
       FROM users u 
       LEFT JOIN profiles p ON u.id = p.id 
       WHERE u.email = $1`, 
      [email]
    )
    
    if (existingUsers.length > 0) {
      const existingRole = existingUsers[0].role
      return NextResponse.json({ 
        error: `This email is already registered as a ${existingRole}. You cannot create a second account with the same email.` 
      }, { status: 400 })
    }

    // Explicitly generate salt
    const saltRounds = 10
    const salt = await bcrypt.genSalt(saltRounds)
    const passwordHash = await bcrypt.hash(password, salt)

    // Directly insert into main users table
    const { rows: userRows } = await query(
      `INSERT INTO users (email, password_hash, salt, is_email_verified) 
       VALUES ($1, $2, $3, $4) RETURNING id`,
      [email, passwordHash, salt, true] // Setting is_email_verified to true since we removed OTP
    )
    
    const userId = userRows[0].id

    // Insert profile
    await query(
      'INSERT INTO profiles (id, full_name, role) VALUES ($1, $2, $3)',
      [userId, fullName || '', role]
    )

    return NextResponse.json({ success: true, requiresVerification: false })
  } catch (error: any) {
    console.error('Signup error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
