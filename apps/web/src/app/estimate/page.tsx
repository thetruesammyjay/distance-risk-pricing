'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { HugeiconsIcon } from '@hugeicons/react';
import { ArrowUpDownIcon, ArrowUpRight01Icon, Clock01Icon, Location01Icon } from '@hugeicons/core-free-icons';
import { QuoteSummary } from '@/components/quote-summary';
import { RoutePreview } from '@/components/route-preview';
import { estimateFare, getLocations } from '@/services/api/client';
import type { FareQuote, LocationOption } from '@/types/api';

export default function EstimatePage() {
  const [locations, setLocations] = useState<LocationOption[]>([]);
  const [originId, setOriginId] = useState('');
  const [destinationId, setDestinationId] = useState('');
  const [requestedAt, setRequestedAt] = useState(new Date().toISOString().slice(0, 16));
  const [quote, setQuote] = useState<FareQuote | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [locationsLoading, setLocationsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getLocations()
      .then((loadedLocations) => {
        if (!active) return;
        setLocations(loadedLocations);
        const defaultOrigin = loadedLocations.find((location) => location.endpoint_name === 'FUTO Main Gate') ?? loadedLocations[0];
        const defaultDestination = loadedLocations.find((location) => location.endpoint_name === 'FUTO Back Gate') ?? loadedLocations[1];
        setOriginId(defaultOrigin?.location_id ?? '');
        setDestinationId(defaultDestination?.location_id ?? '');
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : 'The FUTO locations could not be loaded.');
      })
      .finally(() => {
        if (active) setLocationsLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const origin = useMemo(() => locations.find((location) => location.location_id === originId), [locations, originId]);
  const destination = useMemo(() => locations.find((location) => location.location_id === destinationId), [locations, destinationId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!origin || !destination || origin.location_id === destination.location_id) {
      setError('Select two different FUTO endpoints.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      setQuote(await estimateFare({
        origin: { latitude: origin.latitude, longitude: origin.longitude },
        destination: { latitude: destination.latitude, longitude: destination.longitude },
        requested_at: new Date(requestedAt).toISOString(),
      }));
    } catch (caught) {
      setQuote(null);
      setError(caught instanceof Error ? caught.message : 'The fare could not be estimated.');
    } finally {
      setLoading(false);
    }
  }

  function swapLocations() {
    setOriginId(destinationId);
    setDestinationId(originId);
  }

  return (
    <main className="min-h-[calc(100vh-104px)] bg-fog">
      <div className="mx-auto max-w-[1200px] px-5 py-12 sm:px-8 sm:py-20">
        <div className="max-w-[700px]"><p className="eyebrow text-violet">FUTO fare estimator</p><h1 className="display-face mt-4 text-4xl leading-[1.08] text-ink sm:text-6xl">Price a route with its assumptions visible.</h1><p className="mt-5 max-w-[620px] text-base leading-7 text-slate sm:text-lg">Choose two supplied FUTO endpoints and a trip time. The backend combines authoritative route distance with the active risk, demand, and pricing inputs.</p></div>

        <div className="mt-12 grid gap-8 lg:grid-cols-[.78fr_1.22fr] lg:items-start">
          <form onSubmit={submit} className="card-shadow rounded-[48px] bg-paper p-6 sm:p-10">
            <div className="flex items-start justify-between gap-5 border-b border-ash pb-6"><div><p className="eyebrow text-slate">Trip details</p><h2 className="display-face mt-2 text-2xl text-ink">Choose FUTO endpoints</h2></div><span className="grid h-10 w-10 place-items-center rounded-full bg-lilac text-sm font-medium text-violet">01</span></div>
            <div className="mt-7 space-y-6">
              <LocationFields label="Origin" value={originId} locations={locations} loading={locationsLoading} onChange={setOriginId} />
              <button type="button" onClick={swapLocations} disabled={!origin || !destination} className="inline-flex min-h-11 items-center gap-2 rounded-full border border-ash px-4 text-sm font-medium text-slate transition hover:border-violet hover:text-violet disabled:cursor-not-allowed disabled:opacity-50"><HugeiconsIcon icon={ArrowUpDownIcon} size={17} strokeWidth={1.8} /> Swap locations</button>
              <LocationFields label="Destination" value={destinationId} locations={locations} loading={locationsLoading} onChange={setDestinationId} />
              <label className="block text-sm font-medium text-ink"><span className="flex items-center gap-2"><HugeiconsIcon icon={Clock01Icon} size={17} strokeWidth={1.8} /> Requested trip time</span><span className="mt-2 block text-xs font-normal text-slate">Used to look up time-sensitive inputs.</span><input type="datetime-local" value={requestedAt} onChange={(event) => setRequestedAt(event.target.value)} className="mt-3 min-h-12 w-full rounded-control border border-ash bg-paper px-3 py-2.5 text-sm text-ink outline-none transition focus:border-violet focus:ring-4 focus:ring-violet/10" required /></label>
            </div>
            {error && <div role="alert" className="mt-6 rounded-control border border-crimson/25 bg-crimson/5 px-4 py-3 text-sm leading-6 text-crimson">{error}</div>}
            <button disabled={loading || locationsLoading || !origin || !destination} className="mt-7 flex min-h-14 w-full items-center justify-center rounded-control bg-ink px-4 py-3 text-sm font-medium text-paper transition hover:-translate-y-0.5 hover:bg-violet disabled:cursor-wait disabled:opacity-60">{loading ? 'Calculating route…' : locationsLoading ? 'Loading FUTO endpoints…' : 'Estimate fare'}<HugeiconsIcon icon={ArrowUpRight01Icon} size={17} strokeWidth={1.8} className="ml-3" /></button>
            <p className="mt-5 text-xs leading-5 text-slate">Endpoints come from the supplied FUTO coordinate collection. Source links and collection notes remain attached to the location catalog.</p>
          </form>

          <div className="space-y-6" aria-live="polite">{origin && destination ? <RoutePreview origin={origin} destination={destination} /> : <div className="rounded-[48px] border border-dashed border-ash bg-paper/60 p-8 sm:p-10"><p className="eyebrow text-slate">FUTO endpoints</p><p className="display-face mt-4 text-3xl text-ink">Loading the supplied locations.</p><p className="mt-3 max-w-md text-sm leading-6 text-slate">The estimator will use the real endpoint coordinates from the project dataset.</p></div>}{quote ? <QuoteSummary quote={quote} /> : <div className="rounded-[48px] border border-dashed border-ash bg-paper/60 p-8 sm:p-10"><p className="eyebrow text-slate">Your result</p><p className="display-face mt-4 text-3xl text-ink">The quote will land here.</p><p className="mt-3 max-w-md text-sm leading-6 text-slate">You’ll see the route, risk context, demand scenario, and fare components together.</p></div>}</div>
        </div>
      </div>
    </main>
  );
}

function LocationFields({ label, value, locations, loading, onChange }: { label: string; value: string; locations: LocationOption[]; loading: boolean; onChange: (value: string) => void }) {
  const selected = locations.find((location) => location.location_id === value);
  return <fieldset><legend className="flex items-center gap-2 text-sm font-medium text-ink"><HugeiconsIcon icon={Location01Icon} size={17} strokeWidth={1.8} /> {label}</legend><select aria-label={`${label} endpoint`} value={value} onChange={(event) => onChange(event.target.value)} disabled={loading} className="mt-3 min-h-12 w-full rounded-control border border-ash bg-paper px-3 py-2.5 text-sm text-ink outline-none transition focus:border-violet focus:ring-4 focus:ring-violet/10" required><option value="">{loading ? 'Loading FUTO endpoints…' : 'Select an endpoint'}</option>{locations.map((location) => <option key={location.location_id} value={location.location_id}>{location.endpoint_name}{location.notes ? ` — ${location.notes}` : ''}</option>)}</select>{selected ? <p className="mt-2 text-xs leading-5 text-slate">{selected.latitude.toFixed(7)}, {selected.longitude.toFixed(7)} · {selected.source}</p> : null}</fieldset>;
}
