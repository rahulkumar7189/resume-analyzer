import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth/next'
import { authOptions } from '@/lib/auth'
import { query } from '@/lib/db'
import speakeasy from 'speakeasy'
import QRCode from 'qrcode'

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions)
    if (!session?.user?.email) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const email = session.user.email

    // Generate a new TOTP secret
    const secretInfo = speakeasy.generateSecret({ name: 'AntigravityATS (' + email + ')' })
    const secret = secretInfo.base32

    // Create the otpauth:// URI
    const otpauthUrl = secretInfo.otpauth_url || ''

    // Generate QR code as data URI
    const qrCodeUrl = await QRCode.toDataURL(otpauthUrl)

    // Store the temporary secret in the database (we will verify it in another route before enabling)
    // Actually, we can just return it to the client, and they send it back with the code to verify.
    // But it's safer to store it as a temporary field, or we can just expect the client to send it back.
    // Let's store it directly as totp_secret but set two_factor_enabled = false until verified.
    
    await query(`
      UPDATE users 
      SET totp_secret = $1, two_factor_enabled = false, two_factor_method = 'totp'
      WHERE email = $2
    `, [secret, email])

    return NextResponse.json({ secret, qrCodeUrl })

  } catch (error) {
    console.error('Error setting up 2FA:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}
