import Link from 'next/link';
import { HugeiconsIcon } from '@hugeicons/react';
import { ArrowUpRight01Icon } from '@hugeicons/core-free-icons';

export default function HomePage() {
  return (
    <main>
      <section className="hero-grid overflow-hidden bg-violet text-paper">
        <div className="mx-auto grid max-w-[1200px] gap-14 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-[.86fr_1.14fr] lg:items-center lg:gap-10 lg:py-28">
          <div className="relative z-10 max-w-[560px]">
            <p className="eyebrow text-lemon">A clearer trip estimate</p>
            <h1 className="display-face mt-5 text-[clamp(3.25rem,7vw,5rem)] leading-[1.02] text-paper">See what shapes the fare.</h1>
            <p className="mt-6 max-w-[490px] text-lg leading-[1.6] text-paper/80 sm:text-xl">Distance / Risk makes the route, risk inputs, and demand conditions visible before a price becomes a number.</p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link href="/estimate" className="inline-flex min-h-12 items-center justify-center rounded-control bg-paper px-5 py-3 text-sm font-medium text-ink transition hover:-translate-y-0.5 hover:bg-lemon">Estimate a fare <HugeiconsIcon icon={ArrowUpRight01Icon} size={17} strokeWidth={1.8} className="ml-3" /></Link>
              <Link href="/methodology" className="inline-flex min-h-12 items-center justify-center rounded-control border border-paper/40 px-5 py-3 text-sm font-medium text-paper transition hover:border-paper hover:bg-paper/10">How the model works</Link>
            </div>
            <p className="mt-6 max-w-sm text-xs leading-5 text-paper/60">Experimental research software. Estimates are not official tariffs or safety guarantees.</p>
          </div>
          <FareConsole />
        </div>
      </section>

      <section className="border-b border-ash bg-paper">
        <div className="mx-auto grid max-w-[1200px] gap-6 px-5 py-8 sm:grid-cols-3 sm:px-8">
          <Stat value="01" label="Route distance" detail="The backend calculates the authoritative trip length." />
          <Stat value="02" label="Risk context" detail="Components stay separate, labelled, and traceable." />
          <Stat value="03" label="Demand pressure" detail="The active scenario is returned with the quote." />
        </div>
      </section>

      <section className="mx-auto max-w-[1200px] px-5 py-20 sm:px-8 sm:py-28">
        <div className="max-w-[620px]">
          <p className="eyebrow text-slate">One number, four reasons</p>
          <h2 className="display-face mt-4 text-4xl leading-[1.08] text-ink sm:text-5xl">A fare you can inspect, not just accept.</h2>
        </div>
        <div className="mt-12 grid gap-5 md:grid-cols-3">
          <FeatureCard index="A" title="Distance" text="Use the route distance and duration returned by the routing service—not a browser-side guess." accent="bg-lilac" />
          <FeatureCard index="B" title="Risk" text="Keep accident exposure, road conditions, and perceived security distinct in the explanation." accent="bg-lemon" />
          <FeatureCard index="C" title="Demand" text="Show the supply-and-request scenario that moves the multiplier, including its source label." accent="bg-orchid" />
        </div>
      </section>

      <section className="bg-fog px-5 py-20 sm:px-8 sm:py-24">
        <div className="mx-auto grid max-w-[1200px] gap-10 rounded-[48px] bg-ink px-6 py-10 text-paper sm:px-12 sm:py-14 lg:grid-cols-[1fr_auto] lg:items-center">
          <div className="max-w-[650px]"><p className="eyebrow text-lemon">Start with a route</p><h2 className="display-face mt-4 text-4xl leading-[1.08] sm:text-5xl">Make the assumptions visible.</h2><p className="mt-5 max-w-xl text-base leading-7 text-paper/65">Enter two points and a trip time. The quote keeps its calculation trail attached.</p></div>
          <Link href="/estimate" className="inline-flex min-h-12 items-center justify-center rounded-[32px] bg-paper px-6 py-3 text-sm font-medium text-ink transition hover:bg-lemon">Open the estimator <HugeiconsIcon icon={ArrowUpRight01Icon} size={17} strokeWidth={1.8} className="ml-3" /></Link>
        </div>
      </section>
    </main>
  );
}

function FareConsole() {
  return <div className="console-shadow relative mx-auto w-full max-w-[600px] rotate-1 rounded-[28px] bg-paper p-3 text-ink sm:rounded-[36px] sm:p-5 lg:rotate-2">
    <div className="rounded-[21px] bg-fog p-4 sm:rounded-[28px] sm:p-6">
      <div className="flex items-center justify-between border-b border-ash pb-4"><div><p className="text-xs font-medium uppercase tracking-[.14em] text-slate">Illustrative quote preview</p><p className="mt-1 text-sm font-medium">FUTO Main Gate → FUTO Back Gate</p></div><span className="rounded-full bg-lilac px-3 py-1 text-xs font-medium text-violet">Explainable</span></div>
      <div className="mt-5 rounded-[22px] bg-paper p-4 sm:p-5"><div className="relative h-36 overflow-hidden rounded-[16px] bg-[#eee9ff]"><svg viewBox="0 0 600 190" className="h-full w-full" role="img" aria-label="Illustrated route from origin to destination"><path d="M40 145 C130 16 220 185 318 93 S475 34 555 52" fill="none" stroke="#7047eb" strokeWidth="9" strokeLinecap="round" /><circle cx="40" cy="145" r="11" fill="#121217" /><circle cx="555" cy="52" r="11" fill="#ffc233" /><circle cx="40" cy="145" r="20" fill="none" stroke="#121217" strokeOpacity=".18" strokeWidth="2" /><circle cx="555" cy="52" r="20" fill="none" stroke="#5423e7" strokeOpacity=".25" strokeWidth="2" /></svg><div className="absolute bottom-3 left-3 rounded-full bg-paper/90 px-3 py-1 text-[11px] font-medium text-slate">12.8 km · 31 min</div></div><div className="mt-5 grid grid-cols-3 gap-2 border-b border-ash pb-5 text-center"><MiniMetric label="Risk" value="0.58" /><MiniMetric label="Demand" value="1.20×" /><MiniMetric label="Source" value="Labelled" /></div><div className="flex items-end justify-between pt-5"><div><p className="text-xs uppercase tracking-[.14em] text-slate">Estimated total</p><p className="display-face mt-1 text-3xl sm:text-4xl">₦2,840</p></div><span className="rounded-control bg-ink px-3 py-2 text-xs font-medium text-paper">Additive · distance base</span></div></div>
    </div>
  </div>;
}

function MiniMetric({ label, value }: { label: string; value: string }) { return <div><p className="text-[10px] uppercase tracking-[.14em] text-slate">{label}</p><p className="mt-1 text-sm font-medium text-ink">{value}</p></div>; }
function Stat({ value, label, detail }: { value: string; label: string; detail: string }) { return <div className="border-l-2 border-lemon pl-4"><p className="text-xs font-medium tracking-[.14em] text-violet">{value}</p><p className="mt-2 text-sm font-medium text-ink">{label}</p><p className="mt-1 text-sm leading-6 text-slate">{detail}</p></div>; }
function FeatureCard({ index, title, text, accent }: { index: string; title: string; text: string; accent: string }) { return <article className="card-shadow rounded-[48px] bg-paper p-8 sm:p-10"><span className={`grid h-11 w-11 place-items-center rounded-full ${accent} text-sm font-medium text-ink`}>{index}</span><h3 className="display-face mt-8 text-2xl text-ink">{title}</h3><p className="mt-4 text-base leading-7 text-slate">{text}</p></article>; }
