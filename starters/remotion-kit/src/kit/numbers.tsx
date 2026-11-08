import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {FONT_HEAD, FONT_MONO, SAFE, T, s} from '../theme';
import {clamp, easeOut, usePop, useT} from './time';

// A huge number that kicks (scales up and settles) each time it changes.
export const BigNumber: React.FC<{value: number | string; changedAt: number; top: number; size?: number; color?: string; sub?: string}> = ({
  value, changedAt, top, size = 300, color = T.ink, sub,
}) => {
  const frame = useCurrentFrame();
  const kick = interpolate(frame - s(changedAt), [0, 3, 9], [1.35, 1.1, 1], clamp);
  return (
    <div style={{position: 'absolute', top, left: 0, right: 0, textAlign: 'center'}}>
      <div style={{fontFamily: FONT_HEAD, fontWeight: 800, fontSize: size, lineHeight: 0.9, letterSpacing: -size * 0.05, color, transform: `scale(${kick})`}}>{value}</div>
      {sub ? <div style={{fontFamily: FONT_MONO, fontSize: 36, letterSpacing: 10, color: T.accentSoft, marginTop: 14}}>{sub}</div> : null}
    </div>
  );
};

// A counter that steps up by one on each spoken cue: steps = [at('one'), at('two'), ...].
export const StepCounter: React.FC<{steps: number[]; top: number; size?: number; unit?: [string, string]; doneColor?: string}> = ({
  steps, top, size = 250, unit, doneColor = T.accent,
}) => {
  const t = useT();
  const n = steps.filter((x) => t >= x).length;
  const label = unit ? (n === 1 ? unit[0] : unit[1]) : undefined;
  return <BigNumber value={n} changedAt={steps[Math.max(0, n - 1)] ?? 0} top={top} size={size} color={n === steps.length ? doneColor : T.ink} sub={label} />;
};

// A number that rolls from `from` to `to` over `dur` seconds (prices, views, percentages).
export const CountUp: React.FC<{from?: number; to: number; at: number; dur?: number; top: number; size?: number; prefix?: string; suffix?: string; decimals?: number; sub?: string; color?: string}> = ({
  from = 0, to, at, dur = 1.2, top, size = 260, prefix = '', suffix = '', decimals = 0, sub, color = T.ink,
}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [s(at), s(at + dur)], [from, to], {...clamp, easing: easeOut});
  const text = `${prefix}${v.toLocaleString('en-US', {minimumFractionDigits: decimals, maximumFractionDigits: decimals})}${suffix}`;
  return <BigNumber value={text} changedAt={at + dur} top={top} size={size} color={color} sub={sub} />;
};

// "8 PLATFORMS" style stat line that slams in: big number, mono label.
export const StatLine: React.FC<{n: string; label: string; at: number; top: number; color?: string; size?: number}> = ({n, label, at, top, color = T.ink, size = 260}) => {
  const p = usePop(at, 9, 260);
  if (p <= 0.01) return null;
  return (
    <div style={{position: 'absolute', top, left: SAFE.side, right: SAFE.side, display: 'flex', justifyContent: 'center', alignItems: 'baseline', gap: 30,
      transform: `scale(${interpolate(p, [0, 1], [1.8, 1])})`, opacity: Math.min(1, p * 2)}}>
      <div style={{fontFamily: FONT_HEAD, fontWeight: 800, fontSize: size, lineHeight: 1, letterSpacing: -size * 0.04, color}}>{n}</div>
      <div style={{fontFamily: FONT_MONO, fontSize: 52, letterSpacing: 10, color: T.ink}}>{label}</div>
    </div>
  );
};
