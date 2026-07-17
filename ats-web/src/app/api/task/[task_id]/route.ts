import { NextResponse } from 'next/server';
import { grpcClient } from '@/lib/grpc_client';
import { getServerSession } from "next-auth/next";
import { authOptions } from '@/lib/auth';
import { rateLimit } from '@/lib/rate_limit';

export async function GET(
  req: Request,
  { params }: { params: Promise<{ task_id: string }> }
) {
  // 1. Enforce Authentication
  const session = await getServerSession(authOptions);
  if (!session || !session.user) {
    return NextResponse.json({ detail: 'Unauthorized' }, { status: 401 });
  }

  // 2. Enforce Rate Limiting (60 requests per minute to allow for polling)
  const identifier = session.user.email || 'unknown';
  const { success, remaining, reset } = rateLimit(`task_poll_${identifier}`, 60, 60000);
  
  if (!success) {
    return NextResponse.json({ detail: 'Too many requests. Please try again later.' }, { 
      status: 429,
      headers: {
        'X-RateLimit-Limit': '60',
        'X-RateLimit-Remaining': remaining.toString(),
        'X-RateLimit-Reset': reset.toString(),
      }
    });
  }

  try {
    const { task_id } = await params;

    return new Promise<Response>((resolve) => {
      grpcClient.GetTaskStatus({ task_id }, (err: any, response: any) => {
        if (err) {
          console.error('[gRPC TaskStatus Error]', err);
          resolve(NextResponse.json({ detail: err.message || 'gRPC Error' }, { status: 500 }));
        } else {
          const resPayload: any = {
            status: response.status,
            state: response.state
          };
          if (response.detail) resPayload.detail = response.detail;
          if (response.new_resume_url) resPayload.new_resume_url = response.new_resume_url;
          if (response.data_inserted_json) {
            try {
              const parsed = JSON.parse(response.data_inserted_json);
              if (Array.isArray(parsed) && parsed.length > 0) {
                if (parsed[0].ats_score !== undefined || parsed[0].candidate_name) {
                  resPayload.data_inserted = parsed;
                } else {
                  resPayload.edits = parsed;
                }
              } else {
                resPayload.data_inserted = parsed;
              }
            } catch (e) {
              resPayload.raw_json = response.data_inserted_json;
            }
          }
          resolve(NextResponse.json(resPayload));
        }
      });
    });

  } catch (error: any) {
    console.error('Task route error:', error);
    return NextResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }
}
