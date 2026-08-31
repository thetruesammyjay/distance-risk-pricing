import Link from 'next/link';
import { HugeiconsIcon } from '@hugeicons/react';
import { ArrowUpRight01Icon } from '@hugeicons/core-free-icons';
import { FareBreakdown } from '@/components/fare-breakdown';
import type { FareQuote } from '@/types/api';

export function QuoteSummary({ quote }: { quote: FareQuote }) {
  return <div className="space-y-6"><section className="rounded-[48px] bg-paper p-6 card-shadow sm:p-8"><div className="grid grid-cols-2 gap-x-5 gap-y-7 sm:grid-cols-4"><Metric label="Distance" value={`${quote.route.distance_km.toFixed(1)} km`} /><Metric label="Duration" value={`${quote.route.estimated_duration_minutes} min`} /><Metric label="Risk score" value={quote.risk.score.toFixed(2)} /><Metric label="Demand" value={`${quote.demand.multiplier.toFixed(2)}×`} /></div><div className="mt-8 flex flex-wrap items-center gap-2 border-t border-ash pt-6"><span className="rounded-full bg-lemon px-3 py-1.5 text-xs font-medium text-ink">{quote.risk.classification} route risk</span><span className="rounded-full bg-lilac px-3 py-1.5 text-xs font-medium text-violet">Risk · {quote.risk.source_type}</span><span className="rounded-full bg-fog px-3 py-1.5 text-xs text-slate">Demand · {quote.demand.source_type}</span></div><Link href={`/quote/${quote.quote_id}`} className="mt-6 inline-flex min-h-11 items-center text-sm font-medium text-violet hover:text-ink">Open quote details <HugeiconsIcon icon={ArrowUpRight01Icon} size={17} strokeWidth={1.8} className="ml-2" /></Link></section><FareBreakdown quote={quote} /></div>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div><p className="text-[11px] font-medium uppercase tracking-[.14em] text-slate">{label}</p><p className="display-face mt-2 text-xl text-ink">{value}</p></div>; }
