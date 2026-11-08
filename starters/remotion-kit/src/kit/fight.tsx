import React from 'react';
import {Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT_MONO, SAFE, T, s} from '../theme';
import {clamp} from './time';

// Pieces for a fighting-game parody: your logo with stick limbs versus a chore.

const limb = {stroke: T.ink, strokeWidth: 12, strokeLinecap: 'round' as const, fill: 'none'};

// The hero: an image (your logo) with legs and arms. `punch` 0..1 extends the front arm.
export const Fighter: React.FC<{src: string; x: number; floor: number; size?: number; punch?: number; cheer?: boolean}> = ({src, x, floor, size = 210, punch = 0, cheer = false}) => {
  const frame = useCurrentFrame();
  const bob = Math.sin(frame / 4) * 6;
  const reach = interpolate(punch, [0, 1], [0, 120]);
  const cx = size / 2;
  return (
    <div style={{position: 'absolute', left: x - size / 2, top: floor - size - 110 + bob, width: size, height: size + 110}}>
      <svg width={size + 160} height={size + 120} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}} aria-hidden="true">
        <line x1={cx - 30} y1={size - 6} x2={cx - 55} y2={size + 100} {...limb} />
        <line x1={cx + 30} y1={size - 6} x2={cx + 55 + Math.sin(frame / 4) * 6} y2={size + 100} {...limb} />
        {cheer ? <line x1={size - 16} y1={size * 0.5} x2={size + 40} y2={size * 0.05} {...limb} /> : <line x1={size - 16} y1={size * 0.55} x2={size + 30 + reach} y2={size * 0.5} {...limb} />}
        {!cheer && punch > 0.3 ? <circle cx={size + 30 + reach} cy={size * 0.5} r={16} fill={T.accent} /> : null}
        <line x1={16} y1={size * 0.55} x2={-34} y2={cheer ? size * 0.05 : size * 0.7} {...limb} />
      </svg>
      <Img src={staticFile(src)} style={{position: 'absolute', left: 0, top: 0, width: size, height: size, borderRadius: size * 0.22}} />
    </div>
  );
};

// The opponent: a card with a glyph and a label on legs. It shakes and flashes on each hit and falls at `ko`.
export const Chore: React.FC<{label: string; glyph: React.ReactNode; x: number; floor: number; enter: number; hits?: number[]; ko?: number; color?: string; size?: number}> = ({
  label, glyph, x, floor, enter, hits = [], ko = 1e9, color = T.ink, size = 300,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < s(enter)) return null;
  const drop = spring({frame: frame - s(enter), fps, config: {damping: 12, stiffness: 160}});
  const last = [...hits].reverse().find((h) => frame >= s(h));
  const since = last === undefined ? 99 : frame - s(last);
  const shake = since < 8 ? Math.sin(since * 3) * 16 : 0;
  const flash = since < 3;
  const fall = interpolate(frame, [s(ko), s(ko) + 12], [0, 88], clamp);
  const fade = interpolate(frame, [s(ko) + 14, s(ko) + 26], [1, 0], clamp);
  const l = {stroke: T.ink, strokeWidth: 12, strokeLinecap: 'round' as const};
  return (
    <div style={{position: 'absolute', left: x - size / 2 + shake, top: floor - size - 110 - (1 - drop) * 900, width: size, height: size + 110, transform: `rotate(${fall}deg)`, transformOrigin: 'bottom right', opacity: fade}}>
      <svg width={size} height={size + 110} style={{position: 'absolute', overflow: 'visible'}} aria-hidden="true">
        <line x1={size / 2 - 50} y1={size - 4} x2={size / 2 - 70} y2={size + 100} {...l} />
        <line x1={size / 2 + 50} y1={size - 4} x2={size / 2 + 70} y2={size + 100} {...l} />
      </svg>
      <div style={{position: 'absolute', width: size, height: size, border: `2px solid ${color}`, background: flash ? T.ink : T.card, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 18}}>
        <div style={{opacity: flash ? 0 : 1}}>{glyph}</div>
        <div style={{fontFamily: FONT_MONO, fontSize: 28, letterSpacing: 3, color: flash ? T.bg : color, textAlign: 'center', lineHeight: 1.3, padding: '0 14px'}}>{label}</div>
      </div>
    </div>
  );
};

// Health bars across the top of the safe zone: you on the left, the chore on the right.
// `health` is 0..1 for the chore; pass hits and the bar drains in steps.
export const Hud: React.FC<{hero: string; foe: string; health: number; top?: number}> = ({hero, foe, health, top = SAFE.top}) => {
  const bar = (label: string, fill: number, color: string, align: 'left' | 'right') => (
    <div style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: align === 'left' ? 'flex-start' : 'flex-end', gap: 12}}>
      <div style={{fontFamily: FONT_MONO, fontSize: 28, letterSpacing: 4, color: T.ink}}>{label}</div>
      <div style={{width: '100%', height: 24, border: `1px solid ${T.ink30}`, display: 'flex', justifyContent: align === 'left' ? 'flex-start' : 'flex-end'}}>
        <div style={{width: `${Math.max(0, fill) * 100}%`, background: color}} />
      </div>
    </div>
  );
  return (
    <div style={{position: 'absolute', left: SAFE.side, right: SAFE.side, top, display: 'flex', alignItems: 'flex-end', gap: 32}}>
      {bar(hero, 1, T.accent, 'left')}
      <div style={{fontFamily: FONT_MONO, fontWeight: 700, fontSize: 40, color: T.accentSoft}}>VS</div>
      {bar(foe, health, health < 0.3 ? T.danger : T.ink, 'right')}
    </div>
  );
};

// Health after a list of hits: each hit drains an equal share, eased over `drain` seconds.
export const healthAt = (t: number, hits: number[], drain = 0.35) =>
  1 - hits.reduce((sum, h) => sum + interpolate(t, [h, h + drain], [0, 1], clamp), 0) / Math.max(1, hits.length);

// Impact burst: radiating lines and accent squares for half a second after `at`.
export const Burst: React.FC<{x: number; y: number; at: number}> = ({x, y, at}) => {
  const frame = useCurrentFrame();
  const t = frame - s(at);
  if (t < 0 || t > 16) return null;
  const r = interpolate(t, [0, 16], [20, 220]);
  const o = interpolate(t, [0, 16], [1, 0]);
  return (
    <svg style={{position: 'absolute', left: x - 260, top: y - 260, overflow: 'visible'}} width={520} height={520} aria-hidden="true">
      {Array.from({length: 12}).map((_, i) => {
        const a = (i / 12) * Math.PI * 2;
        return <line key={i} x1={260 + Math.cos(a) * r * 0.5} y1={260 + Math.sin(a) * r * 0.5} x2={260 + Math.cos(a) * r} y2={260 + Math.sin(a) * r} stroke={T.ink} strokeWidth={8} opacity={o} strokeLinecap="round" />;
      })}
      {Array.from({length: 10}).map((_, i) => {
        const a = (i / 10) * Math.PI * 2 + 0.3;
        const d = r * (0.8 + (i % 3) * 0.25);
        return <rect key={i} x={260 + Math.cos(a) * d} y={260 + Math.sin(a) * d} width={18} height={18} fill={i % 2 ? T.accent : T.accentSoft} opacity={o} />;
      })}
    </svg>
  );
};
