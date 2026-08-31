import { NextRequest, NextResponse } from 'next/server';

const forwardableHeaders = ['content-type', 'x-request-id'];

async function forward(request: NextRequest, path: string[]) {
  const serverUrl = process.env.API_SERVER_URL ?? 'http://localhost:8000';
  const upstreamUrl = `${serverUrl.replace(/\/$/, '')}/${path.join('/')}${request.nextUrl.search}`;
  const headers = new Headers();
  for (const header of forwardableHeaders) {
    const value = request.headers.get(header);
    if (value) headers.set(header, value);
  }
  if (process.env.INTERNAL_API_KEY) headers.set('X-API-Key', process.env.INTERNAL_API_KEY);
  const body = request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.arrayBuffer();
  const response = await fetch(upstreamUrl, { method: request.method, headers, body, cache: 'no-store' });
  const responseHeaders = new Headers();
  const contentType = response.headers.get('content-type');
  const requestId = response.headers.get('x-request-id');
  if (contentType) responseHeaders.set('content-type', contentType);
  if (requestId) responseHeaders.set('x-request-id', requestId);
  return new NextResponse(await response.arrayBuffer(), { status: response.status, headers: responseHeaders });
}

export async function GET(request: NextRequest, context: { params: { path: string[] } }) {
  return forward(request, context.params.path);
}

export async function POST(request: NextRequest, context: { params: { path: string[] } }) {
  return forward(request, context.params.path);
}
