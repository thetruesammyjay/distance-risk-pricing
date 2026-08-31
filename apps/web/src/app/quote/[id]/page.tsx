import { notFound } from 'next/navigation';
import { FareBreakdown } from '@/components/fare-breakdown';
import { getQuote } from '@/services/api/client';

export default async function QuotePage({ params }: { params: { id: string } }) {
  try {
    const quote = await getQuote(params.id);
    return <main className="min-h-[calc(100vh-104px)] bg-fog"><div className="mx-auto max-w-[1100px] px-5 py-12 sm:px-8 sm:py-20"><p className="eyebrow text-violet">Saved fare quote</p><h1 className="display-face mt-4 text-5xl leading-[1.04] text-ink sm:text-6xl">Quote {quote.quote_id.slice(0, 8)}</h1><p className="mt-4 text-sm text-slate">Created {new Date(quote.created_at).toLocaleString()}</p><div className="mt-12 grid gap-6 lg:grid-cols-[.9fr_1.1fr] lg:items-start"><FareBreakdown quote={quote} /><section className="rounded-[48px] bg-paper p-7 card-shadow sm:p-10"><p className="eyebrow text-slate">Calculation inputs</p><dl className="mt-7 space-y-5 text-sm"><Row label="Origin" value={`${quote.origin.latitude}, ${quote.origin.longitude}`} /><Row label="Destination" value={`${quote.destination.latitude}, ${quote.destination.longitude}`} /><Row label="Route" value={`${quote.route.distance_km.toFixed(2)} km · ${quote.route.estimated_duration_minutes} min`} /><Row label="Risk" value={`${quote.risk.classification} (${quote.risk.score.toFixed(3)})`} /><Row label="Demand source" value={quote.demand.source_type} /><Row label="Risk source" value={quote.risk.data_sources.join(', ')} /></dl></section></div></div></main>;
  } catch { notFound(); }
}

function Row({ label, value }: { label: string; value: string }) { return <div><dt className="text-[11px] font-medium uppercase tracking-[.14em] text-slate">{label}</dt><dd className="mt-2 text-ink">{value}</dd></div>; }
