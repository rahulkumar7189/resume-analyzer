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

  // 2. Enforce Rate Limiting (5 requests per minute)
  const identifier = session.user.email || 'unknown';
  const { success, remaining, reset } = rateLimit(`compile_pdf_${identifier}`, 5, 60000);
  
  if (!success) {
    return NextResponse.json({ detail: 'Too many requests. Please try again later.' }, { 
      status: 429,
      headers: {
        'X-RateLimit-Limit': '5',
        'X-RateLimit-Remaining': remaining.toString(),
        'X-RateLimit-Reset': reset.toString(),
      }
    });
  }

  try {
    const payload = await req.json();

    return new Promise<Response>((resolve) => {
      grpcClient.CompilePdf(payload, (err: any, response: any) => {
        if (err) {
          console.error('[gRPC CompilePdf Error]', err);
          resolve(NextResponse.json({ detail: err.message || 'gRPC Error' }, { status: 500 }));
        } else {
          resolve(NextResponse.json({
            status: response.status,
            task_id: response.task_id
          }));
        }
      });
    });

  } catch (error: any) {
    console.error('CompilePdf route error:', error);
    return NextResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }
}
