import { NextResponse } from 'next/server';
import { grpcClient } from '@/lib/grpc_client';
import { getServerSession } from "next-auth/next";
import { authOptions } from '@/lib/auth';
import { rateLimit } from '@/lib/rate_limit';

export async function POST(req: Request) {
  // 1. Enforce Authentication
  const session = await getServerSession(authOptions);
  if (!session || !session.user) {
    return NextResponse.json({ detail: 'Unauthorized' }, { status: 401 });
  }

  // 2. Enforce Rate Limiting (20 requests per minute)
  const identifier = session.user.email || 'unknown';
  const { success, remaining, reset } = rateLimit(`suggest_skill_${identifier}`, 20, 60000);
  
  if (!success) {
    return NextResponse.json({ detail: 'Too many requests. Please try again later.' }, { 
      status: 429,
      headers: {
        'X-RateLimit-Limit': '20',
        'X-RateLimit-Remaining': remaining.toString(),
        'X-RateLimit-Reset': reset.toString(),
      }
    });
  }

  try {
    const { resume_text, skill } = await req.json();

    return new Promise<Response>((resolve) => {
      grpcClient.SuggestSkill({
        resume_text: resume_text || '',
        skill: skill || ''
      }, (err: any, response: any) => {
        if (err) {
          console.error('[gRPC SuggestSkill Error]', err);
          resolve(NextResponse.json({ detail: err.message || 'gRPC Error' }, { status: 500 }));
        } else {
          resolve(NextResponse.json({
            status: response.status,
            suggestion: response.suggestion
          }));
        }
      });
    });

  } catch (error: any) {
    console.error('SuggestSkill route error:', error);
    return NextResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }
}
