import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {FONT_HEAD, FONT_MONO, T, s} from '../theme';
import {clamp, ease, usePop} from '../kit';

// Graphics used by the sample videos to illustrate their own scripts. Replace them with your own.

// A phone outline with the top and bottom bands that platform UI covers.
export const SafeZoneDiagram: React.FC<{at: number; bandsAt: number; top: number; height?: number}> = ({at, bandsAt, top, height = 560}) => {
  const p = usePop(at, 14, 200);
  const frame = useCurrentFrame();
  const b = interpolate(frame, [s(bandsAt), s(bandsAt) + 9], [0, 1], {...clamp, easing: ease});
  const w = height * (9 / 16);
  const band = (y0: number, y1: number) => ({position: 'absolute' as const, left: 0, right: 0, top: `${(y0 / 1920) * 100}%`, height: `${((y1 - y0) / 1920) * 100 * b}%`, background: `${T.danger}55`});
  return (
    <div style={{position: 'absolute', top, left: 0, right: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 50, opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * 80}px)`}}>
      <div style={{position: 'relative', width: w, height, border: `4px solid ${T.ink}`, borderRadius: 36, overflow: 'hidden', background: T.card}}>
        <div style={band(0, 240)} />
        <div style={band(1680, 1920)} />
        <div style={{position: 'absolute', left: 0, right: 0, top: `${(240 / 1920) * 100}%`, height: `${(1440 / 1920) * 100}%`, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: FONT_MONO, fontWeight: 700, fontSize: 30, letterSpacing: 4, color: T.success, opacity: b}}>SAFE</div>
      </div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 26, fontFamily: FONT_MONO, fontSize: 30, letterSpacing: 3, color: T.ink60, opacity: b}}>
        <div><span style={{color: T.danger}}>0-240</span><br />HANDLE, TABS</div>
        <div><span style={{color: T.success}}>240-1680</span><br />YOUR CONTENT</div>
        <div><span style={{color: T.danger}}>1680-1920</span><br />CAPTION, BUTTONS</div>
      </div>
    </div>
  );
};

// A row of audio "clips" with gaps; the gaps close at `cutAt`.
export const PauseCut: React.FC<{at: number; cutAt: number; top: number}> = ({at, cutAt, top}) => {
  const p = usePop(at, 14, 200);
  const frame = useCurrentFrame();
  const k = interpolate(frame, [s(cutAt), s(cutAt) + 12], [1, 0], {...clamp, easing: ease});
  const clips = [150, 90, 210, 120, 170];
  const gaps = [90, 130, 70, 110];
  return (
    <div style={{position: 'absolute', top, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 40, opacity: p}}>
      <div style={{display: 'flex', alignItems: 'center'}}>
        {clips.map((w, i) => (
          <React.Fragment key={i}>
            <div style={{width: w, height: 150, background: T.accent, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-evenly', padding: '0 10px'}}>
              {Array.from({length: Math.round(w / 22)}).map((_, j) => <div key={j} style={{width: 6, height: 30 + ((j * 37 + i * 53) % 90), background: T.bg, borderRadius: 3}} />)}
            </div>
            {i < gaps.length ? (
              <div style={{width: gaps[i] * k, height: 150, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden'}}>
                <div style={{width: '70%', borderTop: `4px dashed ${T.danger}`}} />
              </div>
            ) : null}
          </React.Fragment>
        ))}
      </div>
      <div style={{fontFamily: FONT_MONO, fontSize: 34, letterSpacing: 6, color: k < 0.5 ? T.success : T.danger}}>{k < 0.5 ? 'DEAD AIR: 0.0 S' : 'DEAD AIR: 1.6 S'}</div>
    </div>
  );
};

// A caption mock-up where one word lights up in the accent colour at `accentAt`.
export const CaptionDemo: React.FC<{at: number; accentAt: number; top: number}> = ({at, accentAt, top}) => {
  const p = usePop(at, 14, 200);
  const q = usePop(accentAt, 9, 260);
  const words = ['keep', 'people', 'watching'];
  return (
    <div style={{position: 'absolute', top, left: 60, right: 60, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 50, opacity: p}}>
      <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: 26, fontFamily: FONT_HEAD, fontWeight: 800, fontSize: 96, letterSpacing: -3}}>
        {words.map((w, i) => {
          const accent = i === 2 && q > 0.05;
          return <span key={w} style={{color: accent ? T.accentSoft : T.ink, display: 'inline-block', transform: `scale(${accent ? interpolate(q, [0, 1], [1.3, 1]) : 1})`}}>{w}</span>;
        })}
      </div>
      <div style={{fontFamily: FONT_MONO, fontSize: 32, letterSpacing: 6, color: T.ink60}}>ONE WORD CARRIES THE LINE</div>
    </div>
  );
};
