import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {FONT_HEAD, SAFE, T, W, s} from '../theme';
import {usePop} from './time';

// Listicle header: a giant numeral and the step's title, inside the top of the safe zone.
export const StepHeader: React.FC<{n: number; title: string; at: number; top?: number}> = ({n, title, at, top = SAFE.top + 70}) => {
  const p = usePop(at, 9, 260);
  const q = usePop(at + 0.15, 13, 200);
  return (
    <div style={{position: 'absolute', top, left: SAFE.side, right: SAFE.side, display: 'flex', alignItems: 'center', gap: 34}}>
      <div style={{fontFamily: FONT_HEAD, fontWeight: 800, fontSize: 220, lineHeight: 0.85, letterSpacing: -10, color: T.accent, transform: `scale(${interpolate(p, [0, 1], [2, 1])})`, opacity: Math.min(1, p * 2)}}>{n}</div>
      <div style={{fontFamily: FONT_HEAD, fontWeight: 800, fontSize: 72, lineHeight: 1.02, letterSpacing: -2.5, color: T.ink, opacity: q, transform: `translateX(${(1 - q) * 60}px)`}}>{title}</div>
    </div>
  );
};

// Progress dots, one per step, filled once that step has started.
export const StepDots: React.FC<{at: number[]; top?: number}> = ({at, top = SAFE.top}) => {
  const frame = useCurrentFrame();
  const w = 46;
  const gap = 12;
  return (
    <div style={{position: 'absolute', top, left: (W - (at.length * w + (at.length - 1) * gap)) / 2, display: 'flex', gap}}>
      {at.map((t, i) => <div key={i} style={{width: w, height: 8, background: frame >= s(t) ? T.accent : T.line}} />)}
    </div>
  );
};
