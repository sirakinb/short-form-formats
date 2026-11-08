import React from 'react';
import {Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {FONT_MONO, T, W, s} from '../theme';
import {clamp, ease, usePop} from './time';

// Real screenshots and screen recordings with camera moves. Real UI beats a redrawn mock every time:
// capture it at 2x (headless Chrome, or your phone) and drop it in public/shots or public/clips.

export type Rect = [number, number, number, number]; // x, y, width, height in the source's own pixels
export const PANEL_INSET = 40;
export const PANEL_W = W - PANEL_INSET * 2;

// The rounded panel a screenshot or clip sits in. It rises in at `at`.
export const Panel: React.FC<{top: number; height: number; at: number; children: React.ReactNode; label?: string}> = ({top, height, at, children, label}) => {
  const p = usePop(at, 14, 200);
  return (
    <div style={{position: 'absolute', left: PANEL_INSET, right: PANEL_INSET, top, height, transform: `translateY(${(1 - p) * 120}px) scale(${0.94 + 0.06 * p})`, opacity: Math.min(1, p * 1.6)}}>
      {label ? <div style={{position: 'absolute', top: -52, left: 6, fontFamily: FONT_MONO, fontSize: 28, letterSpacing: 6, color: T.accentSoft}}>{label}</div> : null}
      <div style={{position: 'absolute', inset: 0, borderRadius: 28, overflow: 'hidden', border: `1px solid ${T.line}`, background: T.card}}>{children}</div>
    </div>
  );
};

// Move a camera from one rect to another over [start, end]. Returns the scale and offset that
// fit the current rect inside a box of boxW x boxH.
export const useCamera = (from: Rect, to: Rect, start: number, end: number, boxW: number, boxH: number) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [s(start), s(end)], [0, 1], {...clamp, easing: ease});
  const r = from.map((v, i) => v + (to[i] - v) * p);
  const scale = Math.min(boxW / r[2], boxH / r[3]);
  return {scale, tx: boxW / 2 - (r[0] + r[2] / 2) * scale, ty: boxH / 2 - (r[1] + r[3] / 2) * scale};
};

export type Mark = {rect: Rect; at: number};

// Highlighter boxes that sweep in left to right, drawn in the source's pixel space.
export const Marks: React.FC<{marks: Mark[]; scale: number; color?: string}> = ({marks, scale, color = T.accent}) => {
  const frame = useCurrentFrame();
  return (
    <>
      {marks.map((m, i) => {
        const sweep = interpolate(frame, [s(m.at), s(m.at) + 7], [0, 1], {...clamp, easing: ease});
        if (sweep <= 0) return null;
        const pad = 8 / scale;
        return (
          <div key={i} style={{position: 'absolute', left: m.rect[0] - pad, top: m.rect[1] - pad, width: (m.rect[2] + pad * 2) * sweep, height: m.rect[3] + pad * 2,
            background: `${color}33`, border: `${4 / scale}px solid ${color}`, borderRadius: 10 / scale}} />
        );
      })}
    </>
  );
};

// A screenshot from public/ with a camera move and highlight marks. `natW` is the image's pixel width.
// Put it inside a Panel and pass the panel's height as boxH.
export const Shot: React.FC<{src: string; natW: number; from: Rect; to: Rect; start: number; end: number; boxH: number; boxW?: number; marks?: Mark[]}> = ({
  src, natW, from, to, start, end, boxH, boxW = PANEL_W, marks = [],
}) => {
  const c = useCamera(from, to, start, end, boxW, boxH);
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: natW, transform: `translate(${c.tx}px, ${c.ty}px) scale(${c.scale})`, transformOrigin: '0 0'}}>
      <Img src={staticFile(src)} style={{width: natW, display: 'block'}} />
      <Marks marks={marks} scale={c.scale} />
    </div>
  );
};

// A screen recording or b-roll clip with a camera move. It starts playing at `start`; `offset` is the
// second of the clip shown at that moment.
export const Clip: React.FC<{src: string; natW?: number; natH?: number; from: Rect; to: Rect; start: number; end: number; boxH: number; boxW?: number; offset?: number; marks?: Mark[]}> = ({
  src, natW = 1920, natH = 1080, from, to, start, end, boxH, boxW = PANEL_W, offset = 0, marks = [],
}) => {
  const c = useCamera(from, to, start, end, boxW, boxH);
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: natW, height: natH, transform: `translate(${c.tx}px, ${c.ty}px) scale(${c.scale})`, transformOrigin: '0 0'}}>
      <Sequence from={s(start)} layout="none">
        <OffthreadVideo src={staticFile(src)} startFrom={s(offset)} muted style={{width: natW, height: natH}} />
      </Sequence>
      <Marks marks={marks} scale={c.scale} />
    </div>
  );
};
