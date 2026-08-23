import Link from 'next/link';

export function SiteHeader() {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Link href="/" className="font-semibold tracking-tight text-ink">Distance / Risk</Link>
        <nav className="flex gap-5 text-sm text-slate-600" aria-label="Primary navigation">
          <Link href="/estimate" className="hover:text-teal">Estimate</Link>
          <Link href="/risk" className="hover:text-teal">Risk</Link>
          <Link href="/methodology" className="hover:text-teal">Methodology</Link>
          <Link href="/about" className="hover:text-teal">About</Link>
        </nav>
      </div>
    </header>
  );
}

