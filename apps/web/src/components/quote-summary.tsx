import Link from 'next/link';
import type { FareQuote } from '@/types/api';
import { FareBreakdown } from '@/components/fare-breakdown';

export function QuoteSummary({ quote }: { quote: FareQuote }) {
  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_0.8fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="grid grid-cols-2 gap-5 sm:grid-cols-4">
          <Metric label="Distance" value={`${quote.route.distance_km.toFixed(1)} km`} />
          <Metric label="Duration" value={`${quote.route.estimated_duration_minutes} min`} />
          <Metric label="Risk score" value={quote.risk.score.toFixed(2)} />
          <Metric label="Demand" value={`${quote.demand.multiplier.toFixed(2)}×`} />
        </div>
        <div className="mt-7 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-5">
          <span className="rounded-full bg-amber/10 px-3 py-1 text-sm font-medium text-amber">{quote.risk.classification} route risk</span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">Risk: {quote.risk.data_sources.join(', ')}</span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">Demand: {quote.demand.source_type}</span>
        </div>
        <Link href={`/quote/${quote.quote_id}`} className="mt-6 inline-block text-sm font-medium text-teal hover:underline">Open quote details →</Link>
      </section>
      <FareBreakdown quote={quote} />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div><p className="text-xs uppercase tracking-wide text-slate-400">{label}</p><p className="mt-1 text-lg font-semibold text-ink">{value}</p></div>;
}

