import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {BRAND, FONT_MONO, H, SAFE, T, W} from '../theme';

// Thin progress line across the very top. Decorative, so it may sit outside the safe zone.
export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return <div style={{position: 'absolute', top: 0, left: 0, height: 6, width: `${(frame / durationInFrames) * 100}%`, background: T.accent}} />;
};

// Brand URL just inside the bottom of the safe zone.
export const Footer: React.FC<{text?: string}> = ({text = BRAND.url}) => (
  <div style={{position: 'absolute', top: SAFE.bottom - 70, left: 0, right: 0, textAlign: 'center', fontFamily: FONT_MONO, fontSize: 26, letterSpacing: 6, color: T.ink40}}>
    {text.toUpperCase()}
  </div>
);

// Turn on while you edit (showSafeZone prop) to see where platform UI will cover the frame.
export const SafeZoneGuide: React.FC = () => (
  <>
    <div style={{position: 'absolute', left: 0, top: 0, width: W, height: SAFE.top, background: 'rgba(255,0,0,0.25)'}} />
    <div style={{position: 'absolute', left: 0, top: SAFE.bottom, width: W, height: H - SAFE.bottom, background: 'rgba(255,0,0,0.25)'}} />
    <div style={{position: 'absolute', left: SAFE.side, top: SAFE.top, width: W - SAFE.side * 2, height: SAFE.bottom - SAFE.top, outline: '2px dashed rgba(255,0,0,0.7)'}} />
  </>
);
