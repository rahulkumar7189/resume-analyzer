import { NextResponse } from 'next/server';
import { grpcClient } from '@/lib/grpc_client';

export async function POST(req: Request) {
  console.log("RECEIVED ANALYZE REQUEST");
  try {
    const formData = await req.formData();
    const file = formData.get('resume') as File;
    const jobDescription = formData.get('job_description') as string || '';
    const jobId = formData.get('job_id') as string || '';
    const recruiterId = formData.get('recruiter_id') as string || '';
    const candidateEmail = formData.get('candidate_email') as string || '';

    if (!file) {
      return NextResponse.json({ detail: 'No resume provided' }, { status: 400 });
    }

    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);

    return new Promise<Response>((resolve) => {
      grpcClient.AnalyzeResume({
        file_chunk: Buffer.from(bytes),
        file_name: file.name,
        job_description: jobDescription,
        job_id: jobId,
        recruiter_id: recruiterId,
        candidate_email: candidateEmail
      }, (err: any, response: any) => {
        if (err) {
          console.error('[gRPC Analyze Error]', err);
          resolve(NextResponse.json({ detail: err.message || 'gRPC Error' }, { status: 500 }));
        } else {
          resolve(NextResponse.json({
            status: response.status,
            task_id: response.task_id,
            detail: response.detail
          }));
        }
      });
    });

  } catch (error: any) {
    console.error('Analyze route error:', error);
    return NextResponse.json({ detail: 'Internal server error' }, { status: 500 });
  }
}
