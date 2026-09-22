import type { FareQuote } from '@/types/api';

function money(value: number, currency: string) {
  return new Intl.NumberFormat('en-NG', { style: 'currency', currency, maximumFractionDigits: 2 }).format(value);
}

export function FareBreakdown({ quote }: { quote: FareQuote }) {
  const items = [['Distance-adjusted base fare', quote.fare.base_fare], ['Route risk adjustment', quote.fare.risk_adjustment], ['Demand adjustment', quote.fare.demand_adjustment]] as const;
  return <section className="rounded-[48px] bg-paper p-6 card-shadow sm:p-8"><div className="flex items-start justify-between gap-4"><div><p className="eyebrow text-slate">Estimated fare</p><p className="display-face mt-3 text-4xl text-ink">{money(quote.fare.total, quote.fare.currency)}</p></div><span className="rounded-control bg-ink px-3 py-2 text-xs font-medium text-paper">{quote.fare.formula_mode}</span></div><div className="mt-7 space-y-3 border-t border-ash pt-5 text-sm">{items.map(([label, value]) => <div key={label} className="flex items-center justify-between gap-4 text-slate"><span>{label}</span><span className="font-medium text-ink">{money(value, quote.fare.currency)}</span></div>)}</div><p className="mt-4 text-xs leading-5 text-slate">The base fare includes the distance charge, subject to the configured minimum.</p><div className="mt-7 rounded-[24px] bg-fog p-4"><p className="text-xs leading-5 text-slate">Formula <span className="font-medium text-ink">{quote.fare.formula_version}</span> · coefficients <span className="font-medium text-ink">{quote.fare.coefficient_version}</span></p><p className="mt-2 text-xs leading-5 text-slate">Prototype values require empirical calibration.</p></div></section>;
}
