import {continueRender, delayRender} from 'remotion';
import {BRAND} from './theme';

// Loads the brand fonts from brand.fonts.googleFontsUrl before any frame renders.
// Rendering needs network access for this; if the fetch fails the render goes on with system fonts.
// To work offline, put .woff2 files in public/fonts and swap this for FontFace loads with staticFile().
let started = false;

export const loadBrandFonts = () => {
  if (started || typeof document === 'undefined') return;
  started = true;
  const handle = delayRender('Loading brand fonts', {timeoutInMilliseconds: 20000});
  const done = () => continueRender(handle);
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = BRAND.fonts.googleFontsUrl;
  link.onload = () => {
    const {head, body, mono} = BRAND.fonts;
    const wanted = [`800 100px "${head}"`, `700 100px "${head}"`, `400 100px "${body}"`, `500 100px "${mono}"`, `700 100px "${mono}"`];
    Promise.all(wanted.map((f) => document.fonts.load(f))).then(done, done);
  };
  link.onerror = done;
  document.head.appendChild(link);
};
