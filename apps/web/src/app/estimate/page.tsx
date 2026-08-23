'use client';

import { FormEvent, useState } from 'react';
import { estimateFare } from '@/services/api/client';
import { RoutePreview } from '@/components/route-preview';
import { QuoteSummary } from '@/components/quote-summary';
import type { Coordinate, FareQuote } from '@/types/api';

const defaultOrigin: Coordinate = { latitude: 5.3921, longitude: 7.0337 };
const defaultDestination: Coordinate = { latitude: 5.4865, longitude: 7.0259 };

export default function EstimatePage() {
  const [origin, setOrigin] = useState(defaultOrigin);
  const [destination, setDestination] = useState(defaultDestination);
  const [requestedAt, setRequestedAt] = useState(new Date().toISOString().slice(0, 16));
  const [quote, setQuote] = useState<FareQuote | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setLoading(true);
    try { setQuote(await estimateFare({ origin, destination, requested_at: new Date(requestedAt).toISOString() })); }
    catch (caught) { setQuote(null); setError(caught instanceof Error ? caught.message : 'The fare could not be estimated.'); }
    finally { setLoading(false); }
  }

  return <main className="mx-auto max-w-6xl px-6 py-12"><div className="max-w-2xl"><p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Fare estimator</p><h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink">Price a route with its assumptions visible.</h1><p className="mt-4 leading-7 text-slate-600">The backend calculates the authoritative route distance, then combines configured risk and demand inputs with the active pricing formula.</p></div><div className="mt-9 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]"><form onSubmit={submit} className="space-y-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-soft"><LocationFields label="Origin" value={origin} onChange={setOrigin} /><LocationFields label="Destination" value={destination} onChange={setDestination} /><label className="block text-sm font-medium text-ink">Requested trip time<input type="datetime-local" value={requestedAt} onChange={(event) => setRequestedAt(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-teal focus:ring-2 focus:ring-teal/20" required /></label>{error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}<button disabled={loading} className="w-full rounded-lg bg-ink px-4 py-3 text-sm font-medium text-white hover:bg-teal disabled:cursor-wait disabled:opacity-60">{loading ? 'Calculating route…' : 'Estimate fare'}</button><p className="text-xs leading-5 text-slate-500">Risk and demand simulation is clearly labelled until research data sources are configured.</p></form><div className="space-y-6"><RoutePreview origin={origin} destination={destination} />{quote ? <QuoteSummary quote={quote} /> : <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 p-8 text-center text-sm text-slate-500">Your route summary and fare breakdown will appear here.</div>}</div></div></main>;
}

function LocationFields({ label, value, onChange }: { label: string; value: Coordinate; onChange: (value: Coordinate) => void }) {
  return <fieldset><legend className="text-sm font-medium text-ink">{label}</legend><div className="mt-2 grid grid-cols-2 gap-3"><input aria-label={`${label} latitude`} type="number" step="any" min="-90" max="90" value={value.latitude} onChange={(event) => onChange({ ...value, latitude: Number(event.target.value) })} className="rounded-lg border border-slate-300 px-3 py-2.5 text-sm" required /><input aria-label={`${label} longitude`} type="number" step="any" min="-180" max="180" value={value.longitude} onChange={(event) => onChange({ ...value, longitude: Number(event.target.value) })} className="rounded-lg border border-slate-300 px-3 py-2.5 text-sm" required /></div></fieldset>;
}

