import type { FareQuote } from '@/types/api';

function money(value: number, currency: string) {
  return new Intl.NumberFormat('en-NG', { style: 'currency', currency, maximumFractionDigits: 2 }).format(value);
}

export function FareBreakdown({ quote }: { quote: FareQuote }) {
  const items = [
    ['Base fare', quote.fare.base_fare],
    ['Distance component', quote.fare.distance_component],
    ['Route risk adjustment', quote.fare.risk_adjustment],
    ['Demand adjustment', quote.fare.demand_adjustment],
  ] as const;
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div><p className="text-sm text-slate-500">Estimated fare</p><p className="mt-1 text-3xl font-semibold text-ink">{money(quote.fare.total, quote.fare.currency)}</p></div>
        <span className="rounded-full bg-teal/10 px-3 py-1 text-xs font-medium text-teal">{quote.fare.formula_mode}</span>
      </div>
      <div className="space-y-3 border-t border-slate-100 pt-4 text-sm">
        {items.map(([label, value]) => <div key={label} className="flex justify-between text-slate-600"><span>{label}</span><span className="font-medium text-ink">{money(value, quote.fare.currency)}</span></div>)}
      </div>
      <p className="mt-5 text-xs leading-5 text-slate-500">Formula {quote.fare.formula_version} · coefficients {quote.fare.coefficient_version}. Prototype values require empirical calibration.</p>
    </section>
  );
}

