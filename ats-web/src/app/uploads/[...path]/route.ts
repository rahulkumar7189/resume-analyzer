import { NextResponse } from 'next/server';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

export async function GET(
  req: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const resolvedParams = await params;
    const pathArray = resolvedParams.path || [];
    
    // Security check to prevent directory traversal
    if (pathArray.some(p => p.includes('..'))) {
      return new NextResponse('Invalid path', { status: 400 });
    }

    const filePath = join(process.cwd(), 'public', 'uploads', ...pathArray);
    
    if (!existsSync(filePath)) {
      return new NextResponse('File not found', { status: 404 });
    }

    const file = readFileSync(filePath);
    
    // Determine content type
    let contentType = 'application/octet-stream';
    if (filePath.endsWith('.pdf')) contentType = 'application/pdf';
    else if (filePath.endsWith('.png')) contentType = 'image/png';
    else if (filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) contentType = 'image/jpeg';
    else if (filePath.endsWith('.txt')) contentType = 'text/plain';
    else if (filePath.endsWith('.docx')) contentType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

    return new NextResponse(file, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': 'inline', 
      },
    });
  } catch (err) {
    console.error('Error serving file:', err);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
