import React, {useMemo} from 'react';
import {interpolate} from 'remotion';
import {FONT_HEAD, SAFE, T} from '../theme';
import {Word, chunkWords, norm} from '../words';
import {clamp, useT} from './time';

// Word-by-word captions with exactly one accent word on screen at a time.
// If a chunk contains one of `accentWords`, that word stays in the accent colour for the whole chunk
// (pick the one word that carries the line: a number, a product, the payoff). Otherwise the word being
// spoken right now is the accent. Words pop in as they are said.
export const Captions: React.FC<{
  words: Word[];
  top?: number;
  size?: number;
  accentWords?: string[];
  maxWords?: number;
  maxChars?: number;
  look?: 'outline' | 'box';
  hideAfter?: number; // seconds; no captions after this time (for an end card)
}> = ({words, top = 1400, size = 84, accentWords = [], maxWords = 3, maxChars = 17, look = 'outline', hideAfter = 1e9}) => {
  const t = useT();
  const chunks = useMemo(() => chunkWords(words, maxWords, maxChars), [words, maxWords, maxChars]);
  const listed = useMemo(() => new Set(accentWords.map(norm)), [accentWords]);
  if (t > hideAfter) return null;
  const idx = chunks.findIndex((c, i) => t >= c[0].s - 0.05 && (i === chunks.length - 1 || t < chunks[i + 1][0].s - 0.05));
  if (idx < 0) return null;
  const c = chunks[idx];
  if (t > c[c.length - 1].e + 1.2) return null;
  const pinned = c.findIndex((w) => listed.has(norm(w.w)));
  const spoken = c.reduce((k, w, i) => (t >= w.s - 0.04 ? i : k), 0);
  const accentIdx = pinned >= 0 ? pinned : spoken;
  return (
    <div style={{position: 'absolute', left: SAFE.side, right: SAFE.side, top, display: 'flex', justifyContent: 'center'}}>
      <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: size * 0.24, rowGap: 4,
        ...(look === 'box' ? {background: T.scrim, borderRadius: 16, padding: '10px 28px'} : {})}}>
        {c.map((w, i) => {
          if (t < w.s - 0.04) return null;
          const sc = interpolate(t - w.s, [0, 0.08, 0.16], [0.6, 1.12, 1], clamp);
          const accent = i === accentIdx;
          return (
            <span key={i} style={{display: 'inline-block', transform: `scale(${sc})`, transformOrigin: 'center bottom', fontFamily: FONT_HEAD, fontWeight: 800, fontSize: size, lineHeight: 1.08,
              letterSpacing: -size * 0.03, color: accent ? T.accentSoft : T.ink, ...(look === 'outline' ? {WebkitTextStroke: `${size * 0.14}px ${T.bg}`, paintOrder: 'stroke fill'} : {})}}>
              {w.w.replace(/[,;:]$/, '')}
            </span>
          );
        })}
      </div>
    </div>
  );
};
