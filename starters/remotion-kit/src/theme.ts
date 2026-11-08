// The theme is built from the shared brand kit at build time: brand.json is imported straight
// from the repo root (../../brand/brand.json, seen from this starter), so editing it restyles every
// composition the next time the studio reloads or you render. Nothing here is copied by hand.
// The logo file is the one exception: `npm run brand` copies it into public/brand/ (staticFile
// can only serve files from public/). If you move this starter out of the repo, copy brand.json
// next to it and change the import path below.
import brand from '../../../brand/brand.json';

export const BRAND = brand;
export const C = brand.colors;

// Add an alpha channel to a #rrggbb colour: alpha(C.accent, 0.2).
export const alpha = (hex: string, a: number) => {
  const h = hex.replace('#', '');
  const full = h.length === 3 ? h.split('').map((x) => x + x).join('') : h.slice(0, 6);
  return `#${full}${Math.round(Math.max(0, Math.min(1, a)) * 255).toString(16).padStart(2, '0')}`;
};

// Every colour a component uses. Change brand.json, not these lines.
export const T = {
  bg: C.bg,
  card: C.card,
  line: C.line,
  ink: C.ink,
  muted: C.muted,
  accent: C.accent,
  accentStrong: C.accentStrong,
  accentSoft: C.accentSoft,
  success: C.success,
  danger: C.danger,
  accentFaint: alpha(C.accent, 0.2),
  ink60: alpha(C.ink, 0.6),
  ink40: alpha(C.ink, 0.4),
  ink30: alpha(C.ink, 0.3),
  scrim: alpha(C.bg, 0.78),
};

export const FONT_HEAD = `"${brand.fonts.head}", system-ui, sans-serif`;
export const FONT_BODY = `"${brand.fonts.body}", system-ui, sans-serif`;
export const FONT_MONO = `"${brand.fonts.mono}", ui-monospace, monospace`;

// Path of the logo inside public/ after `npm run brand`.
const ext = (brand.logo.match(/\.[a-z0-9]+$/i)?.[0] ?? '.svg').toLowerCase();
export const LOGO = `brand/logo${ext}`;

export const FPS = 30;
export const W = brand.safeZone.width;
export const H = brand.safeZone.height;

// The safe zone: platform UI covers everything above `top` and below `bottom`.
export const SAFE = {top: brand.safeZone.top, bottom: brand.safeZone.bottom, side: 60};

// Seconds to frames.
export const s = (sec: number) => Math.round(sec * FPS);
