'use client';

import { FormEvent, useState } from 'react';
import { HugeiconsIcon } from '@hugeicons/react';
import { ArrowUpDownIcon, ArrowUpRight01Icon, Clock01Icon, Location01Icon } from '@hugeicons/core-free-icons';
import { QuoteSummary } from '@/components/quote-summary';
import { RoutePreview } from '@/components/route-preview';
import { estimateFare } from '@/services/api/client';
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
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      setQuote(await estimateFare({ origin, destination, requested_at: new Date(requestedAt).toISOString() }));
    } catch (caught) {
      setQuote(null);
      setError(caught instanceof Error ? caught.message : 'The fare could not be estimated.');
    } finally {
      setLoading(false);
    }
  }

  function swapLocations() {
    setOrigin(destination);
    setDestination(origin);
  }

  return (
    <main className="min-h-[calc(100vh-104px)] bg-fog">
      <div className="mx-auto max-w-[1200px] px-5 py-12 sm:px-8 sm:py-20">
        <div className="max-w-[700px]"><p className="eyebrow text-violet">Fare estimator</p><h1 className="display-face mt-4 text-4xl leading-[1.08] text-ink sm:text-6xl">Price a route with its assumptions visible.</h1><p className="mt-5 max-w-[620px] text-base leading-7 text-slate sm:text-lg">Enter a route and trip time. The backend combines authoritative distance with the active risk, demand, and pricing inputs.</p></div>

        <div className="mt-12 grid gap-8 lg:grid-cols-[.78fr_1.22fr] lg:items-start">
          <form onSubmit={submit} className="card-shadow rounded-[48px] bg-paper p-6 sm:p-10">
            <div className="flex items-start justify-between gap-5 border-b border-ash pb-6"><div><p className="eyebrow text-slate">Trip details</p><h2 className="display-face mt-2 text-2xl text-ink">Where are you going?</h2></div><span className="grid h-10 w-10 place-items-center rounded-full bg-lilac text-sm font-medium text-violet">01</span></div>
            <div className="mt-7 space-y-6">
              <LocationFields label="Origin" value={origin} onChange={setOrigin} />
              <button type="button" onClick={swapLocations} className="inline-flex min-h-11 items-center gap-2 rounded-full border border-ash px-4 text-sm font-medium text-slate transition hover:border-violet hover:text-violet"><HugeiconsIcon icon={ArrowUpDownIcon} size={17} strokeWidth={1.8} /> Swap locations</button>
              <LocationFields label="Destination" value={destination} onChange={setDestination} />
              <label className="block text-sm font-medium text-ink"><span className="flex items-center gap-2"><HugeiconsIcon icon={Clock01Icon} size={17} strokeWidth={1.8} /> Requested trip time</span><span className="mt-2 block text-xs font-normal text-slate">Used to look up time-sensitive inputs.</span><input type="datetime-local" value={requestedAt} onChange={(event) => setRequestedAt(event.target.value)} className="mt-3 min-h-12 w-full rounded-control border border-ash bg-paper px-3 py-2.5 text-sm text-ink outline-none transition focus:border-violet focus:ring-4 focus:ring-violet/10" required /></label>
            </div>
            {error && <div role="alert" className="mt-6 rounded-control border border-crimson/25 bg-crimson/5 px-4 py-3 text-sm leading-6 text-crimson">{error}</div>}
            <button disabled={loading} className="mt-7 flex min-h-14 w-full items-center justify-center rounded-control bg-ink px-4 py-3 text-sm font-medium text-paper transition hover:-translate-y-0.5 hover:bg-violet disabled:cursor-wait disabled:opacity-60">{loading ? 'Calculating route…' : 'Estimate fare'}<HugeiconsIcon icon={ArrowUpRight01Icon} size={17} strokeWidth={1.8} className="ml-3" /></button>
            <p className="mt-5 text-xs leading-5 text-slate">Simulation inputs are labelled in the result until verified research data sources are connected.</p>
          </form>

          <div className="space-y-6" aria-live="polite"><RoutePreview origin={origin} destination={destination} />{quote ? <QuoteSummary quote={quote} /> : <div className="rounded-[48px] border border-dashed border-ash bg-paper/60 p-8 sm:p-10"><p className="eyebrow text-slate">Your result</p><p className="display-face mt-4 text-3xl text-ink">The quote will land here.</p><p className="mt-3 max-w-md text-sm leading-6 text-slate">You’ll see the route, risk context, demand scenario, and fare components together.</p></div>}</div>
        </div>
      </div>
    </main>
  );
}

function LocationFields({ label, value, onChange }: { label: string; value: Coordinate; onChange: (value: Coordinate) => void }) {
  return <fieldset><legend className="flex items-center gap-2 text-sm font-medium text-ink"><HugeiconsIcon icon={Location01Icon} size={17} strokeWidth={1.8} /> {label}</legend><div className="mt-3 grid grid-cols-2 gap-3"><label className="text-xs text-slate">Latitude<input aria-label={`${label} latitude`} type="number" step="any" min="-90" max="90" value={value.latitude} onChange={(event) => onChange({ ...value, latitude: Number(event.target.value) })} className="mt-2 min-h-12 w-full rounded-control border border-ash bg-paper px-3 py-2.5 text-sm text-ink outline-none transition focus:border-violet focus:ring-4 focus:ring-violet/10" required /></label><label className="text-xs text-slate">Longitude<input aria-label={`${label} longitude`} type="number" step="any" min="-180" max="180" value={value.longitude} onChange={(event) => onChange({ ...value, longitude: Number(event.target.value) })} className="mt-2 min-h-12 w-full rounded-control border border-ash bg-paper px-3 py-2.5 text-sm text-ink outline-none transition focus:border-violet focus:ring-4 focus:ring-violet/10" required /></label></div></fieldset>;
}
