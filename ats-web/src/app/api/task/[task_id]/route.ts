import { NextResponse } from 'next/server';
import { grpcClient } from '@/lib/grpc_client';

export async function GET(
  req: Request,
  { params }: { params: Promise<{ task_id: string }> }
) {
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
