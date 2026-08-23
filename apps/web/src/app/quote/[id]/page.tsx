import { notFound } from 'next/navigation';
import { FareBreakdown } from '@/components/fare-breakdown';
import { getQuote } from '@/services/api/client';

export default async function QuotePage({ params }: { params: { id: string } }) {
  try {
    const quote = await getQuote(params.id);
    return <main className="mx-auto max-w-5xl px-6 py-12"><p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Saved fare quote</p><h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink">Quote {quote.quote_id.slice(0, 8)}</h1><p className="mt-3 text-slate-600">Created {new Date(quote.created_at).toLocaleString()}</p><div className="mt-8 grid gap-6 md:grid-cols-2"><FareBreakdown quote={quote} /><section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft"><h2 className="font-semibold text-ink">Calculation inputs</h2><dl className="mt-5 space-y-4 text-sm"><Row label="Origin" value={`${quote.origin.latitude}, ${quote.origin.longitude}`} /><Row label="Destination" value={`${quote.destination.latitude}, ${quote.destination.longitude}`} /><Row label="Route" value={`${quote.route.distance_km.toFixed(2)} km · ${quote.route.estimated_duration_minutes} min`} /><Row label="Risk" value={`${quote.risk.classification} (${quote.risk.score.toFixed(3)})`} /><Row label="Demand source" value={quote.demand.source_type} /><Row label="Risk source" value={quote.risk.data_sources.join(', ')} /></dl></section></div></main>;
  } catch { notFound(); }
}

function Row({ label, value }: { label: string; value: string }) { return <div><dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt><dd className="mt-1 text-ink">{value}</dd></div>; }

