import { NextResponse } from 'next/server';
import { grpcClient } from '@/lib/grpc_client';

export async function POST(req: Request) {
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
