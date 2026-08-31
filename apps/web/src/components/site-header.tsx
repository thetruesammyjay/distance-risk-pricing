'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';
import { HugeiconsIcon } from '@hugeicons/react';
import { ArrowUpRight01Icon, CancelCircleIcon, Menu01Icon } from '@hugeicons/core-free-icons';
import FarelyticsLogo from '@/Farelytics.png';

const links = [
  { href: '/estimate', label: 'Estimate' },
  { href: '/risk', label: 'Risk model' },
  { href: '/methodology', label: 'Methodology' },
];

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="bg-lemon px-4 py-2 text-center text-[11px] font-medium uppercase tracking-[0.16em] text-ink sm:text-sm">
        Research prototype · transparent fare logic
      </div>
      <header className="sticky top-0 z-40 border-b border-ash bg-paper/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-5 sm:px-8">
          <Link href="/" className="flex items-center" onClick={() => setOpen(false)} aria-label="Farelytics home">
            <Image src={FarelyticsLogo} alt="Farelytics" width={166} height={54} priority className="h-auto w-[138px] sm:w-[166px]" />
          </Link>

          <nav className="hidden items-center gap-1 md:flex" aria-label="Primary navigation">
            {links.map((link) => <Link key={link.href} href={link.href} className="rounded-full px-4 py-2 text-sm font-medium text-slate transition hover:bg-fog hover:text-ink">{link.label}</Link>)}
          </nav>

          <div className="hidden items-center gap-5 md:flex">
            <Link href="/about" className="text-sm font-medium text-slate hover:text-ink">About</Link>
            <Link href="/estimate" className="rounded-control bg-ink px-5 py-3 text-sm font-medium text-paper shadow-sm transition hover:-translate-y-0.5 hover:bg-violet">Start an estimate <HugeiconsIcon icon={ArrowUpRight01Icon} size={16} strokeWidth={1.8} className="ml-2 inline-block" /></Link>
          </div>

          <button type="button" aria-expanded={open} aria-controls="mobile-navigation" className="grid h-11 w-11 place-items-center rounded-control border border-ash text-ink md:hidden" onClick={() => setOpen(!open)}>
            <span className="sr-only">Open navigation</span>
            <HugeiconsIcon icon={open ? CancelCircleIcon : Menu01Icon} size={22} strokeWidth={1.8} aria-hidden="true" />
          </button>
        </div>
        {open && <nav id="mobile-navigation" className="border-t border-ash bg-paper px-5 py-3 md:hidden" aria-label="Mobile navigation">
          {[...links, { href: '/about', label: 'About' }].map((link) => <Link key={link.href} href={link.href} onClick={() => setOpen(false)} className="block border-b border-ash py-4 text-base font-medium text-ink last:border-0">{link.label}</Link>)}
        </nav>}
      </header>
    </>
  );
}
