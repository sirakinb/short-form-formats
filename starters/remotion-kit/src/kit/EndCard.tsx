import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {BRAND, FONT_HEAD, FONT_MONO, LOGO, SAFE, T} from '../theme';
import {usePop} from './time';

// Closing card from brand.json: logo, name, handle, URL and the call to action.
// Say the action out loud as well; the card backs up what you say, it does not replace it.
export const EndCard: React.FC<{at: number; cta?: string; sub?: string; showLogo?: boolean}> = ({at, cta = BRAND.cta.default, sub = BRAND.cta.sub, showLogo = true}) => {
  const p = usePop(at, 10, 140);
  const q = usePop(at + 0.35, 10, 220);
  return (
    <AbsoluteFill style={{background: T.bg}}>
      <div style={{position: 'absolute', top: SAFE.top + 160, left: SAFE.side, right: SAFE.side, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 30}}>
        {showLogo ? <Img src={staticFile(LOGO)} style={{width: 240, height: 240, borderRadius: 54, transform: `scale(${p}) rotate(${(1 - p) * -30}deg)`}} /> : null}
        <div style={{fontFamily: FONT_HEAD, fontWeight: 700, fontSize: 100, letterSpacing: -4, color: T.ink, opacity: p, textAlign: 'center'}}>{BRAND.name}</div>
        <div style={{fontFamily: FONT_MONO, fontSize: 34, letterSpacing: 6, color: T.ink60, opacity: p}}>{BRAND.handle} · {BRAND.url}</div>
        <div style={{marginTop: 30, fontFamily: FONT_MONO, fontWeight: 700, fontSize: 44, letterSpacing: 6, color: T.bg, background: T.accent, padding: '16px 30px', transform: `scale(${q})`}}>{cta.toUpperCase()}</div>
        {sub ? <div style={{fontFamily: FONT_MONO, fontSize: 30, letterSpacing: 6, color: T.accentSoft, opacity: q}}>{sub.toUpperCase()}</div> : null}
      </div>
    </AbsoluteFill>
  );
};
