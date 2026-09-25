import type { ApiError, FareQuote, FareRequest, LocationOption } from '@/types/api';

function endpoint(path: string) {
  if (typeof window === 'undefined') {
    const serverUrl = process.env.API_SERVER_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
    return `${serverUrl}${path}`;
  }
  // Production requests must use the same-origin proxy so the server-only
  // INTERNAL_API_KEY is attached without exposing it to the browser.
  if (process.env.NODE_ENV !== 'production') {
    const browserUrl = process.env.NEXT_PUBLIC_API_URL;
    if (browserUrl) return `${browserUrl}${path}`;
  }
  return `/api/backend${path}`;
}

export async function estimateFare(request: FareRequest): Promise<FareQuote> {
  const response = await fetch(endpoint('/api/v1/fares/estimate'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  const payload = (await response.json()) as FareQuote | ApiError;
  if (!response.ok || 'error' in payload) {
    throw new Error('error' in payload ? payload.error.message : 'The fare could not be estimated.');
  }
  return payload;
}

export async function getLocations(): Promise<LocationOption[]> {
  const response = await fetch(endpoint('/api/v1/locations'), { cache: 'no-store' });
  const payload = (await response.json()) as LocationOption[] | ApiError;
  if (!response.ok || 'error' in payload) {
    throw new Error('error' in payload ? payload.error.message : 'The FUTO locations could not be loaded.');
  }
  return payload;
}

export async function getQuote(id: string): Promise<FareQuote> {
  const response = await fetch(endpoint(`/api/v1/fares/${encodeURIComponent(id)}`), { cache: 'no-store' });
  const payload = (await response.json()) as FareQuote | ApiError;
  if (!response.ok || 'error' in payload) {
    throw new Error('error' in payload ? payload.error.message : 'The quote could not be loaded.');
  }
  return payload;
}
