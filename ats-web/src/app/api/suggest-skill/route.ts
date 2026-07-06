import { NextResponse } from 'next/server';
import { grpcClient } from '@/lib/grpc_client';

export async function POST(req: Request) {
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
