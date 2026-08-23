type Props = { origin: { latitude: number; longitude: number }; destination: { latitude: number; longitude: number } };

export function RoutePreview({ origin, destination }: Props) {
  return (
    <div className="relative min-h-64 overflow-hidden rounded-2xl border border-slate-200 bg-[#eaf2f0] p-5">
      <div className="absolute inset-0 opacity-50 [background-image:linear-gradient(30deg,#c9ddda_1px,transparent_1px),linear-gradient(120deg,#c9ddda_1px,transparent_1px)] [background-size:42px_42px]" />
      <div className="relative flex min-h-52 items-center justify-center">
        <svg viewBox="0 0 600 230" className="h-full w-full" role="img" aria-label="Route preview">
          <path d="M 75 175 C 170 42, 280 210, 370 87 S 500 45, 540 70" fill="none" stroke="#087f8c" strokeWidth="10" strokeLinecap="round" />
          <circle cx="75" cy="175" r="12" fill="#102a43" />
          <circle cx="540" cy="70" r="12" fill="#d97706" />
        </svg>
        <div className="absolute bottom-3 left-3 rounded-lg bg-white/90 px-3 py-2 text-xs text-slate-600 shadow-sm">
          Backend route preview · {origin.latitude.toFixed(3)}, {origin.longitude.toFixed(3)} → {destination.latitude.toFixed(3)}, {destination.longitude.toFixed(3)}
        </div>
      </div>
    </div>
  );
}

