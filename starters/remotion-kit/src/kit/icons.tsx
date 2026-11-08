import React from 'react';
import {T} from '../theme';

// Simple line icons. Use real logos (public/logos) for products and brands; these are for ideas.

export const Check: React.FC<{size: number; color?: string}> = ({size, color = T.success}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={3.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M4 12.5l5 5L20 6.5" />
  </svg>
);

export const Arrow: React.FC<{size: number; color?: string}> = ({size, color = T.accent}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={3.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);

type GlyphFn = (color?: string, size?: number) => React.ReactElement;
const svg = (size: number, children: React.ReactNode, color: string) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
);

export const Glyph: Record<'inbox' | 'calendar' | 'clock' | 'bolt' | 'doc' | 'person', GlyphFn> = {
  inbox: (c = T.ink, n = 120) => svg(n, <><rect x="3" y="5" width="18" height="14" rx="1.5" /><path d="M3 13h5l1.5 2.5h5L16 13h5" /></>, c),
  calendar: (c = T.ink, n = 120) => svg(n, <><rect x="3.5" y="5" width="17" height="15" rx="1.5" /><path d="M3.5 9.5h17M8 3v4M16 3v4M7 13h2M11 13h2M15 13h2M7 16.5h2M11 16.5h2" /></>, c),
  clock: (c = T.ink, n = 120) => svg(n, <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l-3 2" /></>, c),
  bolt: (c = T.danger, n = 120) => svg(n, <path d="M13 3L5 13.5h6L10 21l8-10.5h-6z" />, c),
  doc: (c = T.ink, n = 120) => svg(n, <><path d="M6 3h8l4 4v14H6z" /><path d="M14 3v4h4M9 12h6M9 15.5h6" /></>, c),
  person: (c = T.ink, n = 120) => svg(n, <><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" /></>, c),
};
