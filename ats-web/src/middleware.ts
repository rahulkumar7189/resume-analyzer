import { withAuth } from "next-auth/middleware"

export default withAuth({
  pages: {
    signIn: '/login',
  },
})

export const config = {
  matcher: [
    '/candidate/:path*',
    '/recruiter/:path*',
    '/api/analyze',
    '/api/autofix',
    '/api/suggest-edits',
    '/api/suggest-skill',
    '/api/compile-pdf',
    '/api/task/:path*'
  ],
}
