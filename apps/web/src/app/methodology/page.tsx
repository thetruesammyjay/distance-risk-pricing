const steps = [
  ['01', 'Route distance', 'The routing service obtains the authoritative distance and duration. The browser does not calculate the trip distance.'],
  ['02', 'Route risk', 'Available accident, road, and security components are combined with configured weights. Missing components stay visible.'],
  ['03', 'Demand', 'The current request-to-driver scenario becomes a capped multiplier and travels with its source label.'],
  ['04', 'Pricing', 'The active formula and coefficient version are stored with the quote so the number has a calculation trail.'],
];

export default function MethodologyPage() {
  return <main className="min-h-[calc(100vh-104px)] bg-paper"><div className="mx-auto max-w-[1000px] px-5 py-16 sm:px-8 sm:py-24"><p className="eyebrow text-violet">Methodology</p><h1 className="display-face mt-5 max-w-3xl text-5xl leading-[1.04] text-ink sm:text-7xl">A transparent calculation pipeline.</h1><p className="mt-7 max-w-2xl text-lg leading-8 text-slate">The model is intentionally decomposed. Each stage can be inspected without hiding uncertainty behind a single score.</p><div className="mt-14 space-y-4">{steps.map(([number, title, text]) => <section key={number} className="grid gap-5 rounded-[48px] bg-fog p-7 sm:grid-cols-[80px_220px_1fr] sm:items-start sm:p-10"><span className="display-face text-3xl text-violet">{number}</span><h2 className="display-face text-2xl text-ink">{title}</h2><p className="text-base leading-7 text-slate">{text}</p></section>)}</div><section className="mt-14 rounded-[48px] bg-ink p-8 text-paper sm:p-10"><p className="eyebrow text-lemon">Limitations</p><p className="mt-5 max-w-2xl text-base leading-7 text-paper/70">Prototype coefficients and simulated inputs are not calibrated transportation tariffs or verified safety data. Provenance and calibration are part of the research work.</p></section></div></main>;
}
