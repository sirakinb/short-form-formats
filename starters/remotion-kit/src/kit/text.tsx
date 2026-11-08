import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT_HEAD, FONT_MONO, SAFE, T, s} from '../theme';
import {Arrow} from './icons';
import {clamp, usePop, useT} from './time';

// Small mono label, centred, that fades up at `at`.
export const Label: React.FC<{text: string; at: number; top: number; color?: string; size?: number}> = ({text, at, top, color = T.accentSoft, size = 34}) => {
  const p = usePop(at);
  if (p <= 0.01) return null;
  return (
    <div style={{position: 'absolute', top, left: SAFE.side, right: SAFE.side, textAlign: 'center', fontFamily: FONT_MONO, fontSize: size, letterSpacing: size * 0.25, color, opacity: p, transform: `translateY(${(1 - p) * 20}px)`}}>
      {text}
    </div>
  );
};

// A boxed label pinned near the top of a graphic (inside the safe zone). Use at < 0 to show it with no pop.
export const Tag: React.FC<{text: string; at: number; color?: string; top?: number}> = ({text, at, color = T.accent, top = SAFE.top + 10}) => {
  const frame = useCurrentFrame();
  const p = usePop(at, 12, 240);
  const shown = at < 0 ? 1 : frame >= s(at) ? p : 0;
  if (shown <= 0.01) return null;
  return (
    <div style={{position: 'absolute', top, left: 0, right: 0, display: 'flex', justifyContent: 'center', transform: `scale(${shown})`, zIndex: 5}}>
      <div style={{background: T.bg, border: `2px solid ${color}`, padding: '14px 30px', fontFamily: FONT_MONO, fontWeight: 700, fontSize: 38, letterSpacing: 5, color: T.ink}}>{text}</div>
    </div>
  );
};

// A line of text that slams down from 2x at `at`.
export const Slam: React.FC<{text: string; at: number; top: number; size?: number; color?: string}> = ({text, at, top, size = 150, color = T.ink}) => {
  const p = usePop(at, 9, 240);
  if (p <= 0.01) return null;
  return (
    <div style={{position: 'absolute', top, left: SAFE.side, right: SAFE.side, textAlign: 'center', fontFamily: FONT_HEAD, fontWeight: 800, fontSize: size, lineHeight: 0.98, letterSpacing: -size * 0.04, color,
      transform: `scale(${interpolate(p, [0, 1], [2.2, 1])})`, opacity: Math.min(1, p * 2)}}>
      {text}
    </div>
  );
};

// One huge line filling the frame, with an optional icon above and a mono line below. Drifts in slowly so it never sits still.
export const BigWord: React.FC<{text: string; at: number; icon?: string; sub?: string; size?: number; accent?: boolean; bg?: string}> = ({
  text, at, icon, sub, size = 170, accent, bg = T.bg,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - s(at), fps, config: {damping: 11, stiffness: 240}});
  const lp = spring({frame: frame - s(at) + 3, fps, config: {damping: 12, stiffness: 200}});
  const drift = interpolate(frame, [s(at), s(at) + 60], [1, 1.06], clamp);
  return (
    <AbsoluteFill style={{background: bg, alignItems: 'center', justifyContent: 'center', transform: `scale(${drift})`}}>
      {icon ? (
        <div style={{marginBottom: 60, transform: `scale(${lp})`, width: 220, height: 220, borderRadius: 48, background: T.card, border: `1px solid ${T.line}`, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <Img src={staticFile(icon)} style={{width: 150, height: 150, objectFit: 'contain'}} />
        </div>
      ) : null}
      <div style={{fontFamily: FONT_HEAD, fontWeight: 800, fontSize: size, letterSpacing: -size * 0.045, lineHeight: 0.95, color: accent ? T.accent : T.ink, textAlign: 'center', padding: `0 ${SAFE.side}px`,
        transform: `scale(${interpolate(p, [0, 1], [1.8, 1])})`, opacity: Math.min(1, p * 2)}}>
        {text}
      </div>
      {sub ? <div style={{marginTop: 44, fontFamily: FONT_MONO, fontSize: 40, letterSpacing: 10, color: T.accentSoft, opacity: lp}}>{sub}</div> : null}
    </AbsoluteFill>
  );
};

// A spoken list: each item slides in on its word; the current item is bright, earlier ones dim.
export const WordStack: React.FC<{items: {text: string; at: number}[]; size?: number; paddingTop?: number}> = ({items, size = 104, paddingTop = 120}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = useT();
  return (
    <AbsoluteFill style={{background: T.bg, alignItems: 'center', justifyContent: 'center', paddingTop}}>
      <div style={{display: 'flex', flexDirection: 'column', gap: size * 0.3, alignItems: 'flex-start'}}>
        {items.map((it) => {
          const p = spring({frame: frame - s(it.at), fps, config: {damping: 12, stiffness: 240}});
          const current = t >= it.at && !items.some((o) => o.at > it.at && t >= o.at);
          return (
            <div key={it.text} style={{display: 'flex', alignItems: 'center', gap: size * 0.32, opacity: p > 0.01 ? (current ? 1 : 0.35) : 0,
              transform: `translateX(${(1 - p) * -80}px) scale(${current ? 1 : 0.92})`, transformOrigin: 'left center'}}>
              <div style={{width: size * 0.7, height: size * 0.7, background: T.accent, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <Arrow size={size * 0.42} color={T.bg} />
              </div>
              <div style={{fontFamily: FONT_HEAD, fontWeight: 800, fontSize: size, letterSpacing: -size * 0.03, color: T.ink}}>{it.text}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// A centred banner (ROUND 1, K.O.) that slams in at `from` and fades out at `to`.
export const Banner: React.FC<{text: string; from: number; to?: number; top?: number; size?: number; color?: string; sub?: string}> = ({
  text, from, to = 1e9, top = 600, size = 150, color = T.ink, sub,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < s(from) || frame > s(to)) return null;
  const sc = interpolate(spring({frame: frame - s(from), fps, config: {damping: 9, stiffness: 200}}), [0, 1], [2.4, 1]);
  const op = interpolate(frame, [s(from), s(from) + 3, s(to) - 4, s(to)], [0, 1, 1, 0], clamp);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top, textAlign: 'center', opacity: op, transform: `scale(${sc})`}}>
      <div style={{fontFamily: FONT_HEAD, fontWeight: 800, fontSize: size, letterSpacing: -size * 0.04, lineHeight: 1, color}}>{text}</div>
      {sub ? <div style={{fontFamily: FONT_MONO, fontSize: 38, letterSpacing: 10, color: T.accentSoft, marginTop: 18}}>{sub}</div> : null}
    </div>
  );
};
