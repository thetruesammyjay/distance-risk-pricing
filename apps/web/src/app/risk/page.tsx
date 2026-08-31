const components = [
  ['01', 'Accident exposure', 'Signals associated with incident exposure, returned with their source and model version.'],
  ['02', 'Road conditions', 'The route environment stays separate from the other risk components so it can be evaluated on its own.'],
  ['03', 'Perceived security', 'Questionnaire-derived values describe perception; they are not verified crime probabilities.'],
];

export default function RiskPage() {
  return <main className="min-h-[calc(100vh-104px)] bg-fog"><div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-8 sm:py-24"><div className="max-w-3xl"><p className="eyebrow text-violet">Risk view</p><h1 className="display-face mt-5 text-5xl leading-[1.04] text-ink sm:text-7xl">Risk information needs a label.</h1><p className="mt-7 text-lg leading-8 text-slate">The product keeps risk components separate and tells you where they came from. That distinction matters when a model informs a price.</p></div><div className="mt-14 grid gap-5 md:grid-cols-3">{components.map(([number, title, text]) => <article key={number} className="rounded-[48px] bg-paper p-8 card-shadow sm:p-10"><span className="grid h-12 w-12 place-items-center rounded-full bg-lemon text-sm font-medium text-ink">{number}</span><h2 className="display-face mt-9 text-2xl text-ink">{title}</h2><p className="mt-4 text-base leading-7 text-slate">{text}</p></article>)}</div></div></main>;
}
