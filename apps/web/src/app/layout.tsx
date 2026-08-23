import type { Metadata } from 'next';
import { SiteHeader } from '@/components/site-header';
import './globals.css';

export const metadata: Metadata = {
  title: 'Distance / Risk — Explainable fare estimation',
  description: 'Academic research prototype for transparent distance-risk-aware transportation pricing.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><SiteHeader />{children}</body></html>;
}

