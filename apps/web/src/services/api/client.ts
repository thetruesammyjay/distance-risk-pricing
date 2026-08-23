import type { ApiError, FareQuote, FareRequest } from '@/types/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function estimateFare(request: FareRequest): Promise<FareQuote> {
  const response = await fetch(`${API_URL}/api/v1/fares/estimate`, {
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

export async function getQuote(id: string): Promise<FareQuote> {
  const response = await fetch(`${API_URL}/api/v1/fares/${encodeURIComponent(id)}`, { cache: 'no-store' });
  const payload = (await response.json()) as FareQuote | ApiError;
  if (!response.ok || 'error' in payload) {
    throw new Error('error' in payload ? payload.error.message : 'The quote could not be loaded.');
  }
  return payload;
}

