import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {BRAND, FONT_HEAD, FONT_MONO, LOGO, SAFE, T, W} from '../theme';

// Cover still, 1080x1920. Profile grids crop to roughly the safe zone, so the title, the number
// and the face all sit between y 240 and 1680. Write the title as the promise, in a few words.

export type CoverProps = {
  kicker?: string; // small mono line above the title
  title: string;
  accent?: string; // one word of the title to colour
  big?: string; // optional huge numeral or symbol above the title
  image?: string; // optional picture in public/, e.g. a frame of your take
  logos?: string[]; // optional row of logos in public/
  showSafeZone?: boolean;
};

const Title: React.FC<{title: string; accent?: string; size: number}> = ({title, accent, size}) => (
  <div style={{fontFamily: FONT_HEAD, fontWeight: 800, fontSize: size, lineHeight: 1.0, letterSpacing: -size * 0.04, color: T.ink, textAlign: 'center'}}>
    {title.split(' ').map((w, i, a) => (
      <React.Fragment key={i}>
        <span style={{color: accent && w.toLowerCase().replace(/[^a-z0-9]/g, '') === accent.toLowerCase() ? T.accent : undefined}}>{w}</span>
        {i < a.length - 1 ? ' ' : ''}
      </React.Fragment>
    ))}
  </div>
);

export const Cover: React.FC<CoverProps> = ({kicker, title, accent, big, image, logos = [], showSafeZone = false}) => (
  <AbsoluteFill style={{background: T.bg}}>
    {image ? (
      <>
        <Img src={staticFile(image)} style={{position: 'absolute', left: 0, top: 420, width: W, height: 1920, objectFit: 'cover'}} />
        <AbsoluteFill style={{background: `linear-gradient(to bottom, ${T.bg} 0%, ${T.bg} 30%, transparent 52%, transparent 82%, ${T.bg} 100%)`}} />
      </>
    ) : null}
    <div style={{position: 'absolute', top: SAFE.top + 60, left: SAFE.side, right: SAFE.side, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 34}}>
      {kicker ? <div style={{fontFamily: FONT_MONO, fontSize: 36, letterSpacing: 9, color: T.accentSoft}}>{kicker.toUpperCase()}</div> : null}
      {big ? <div style={{fontFamily: FONT_HEAD, fontWeight: 800, fontSize: 420, lineHeight: 0.85, letterSpacing: -20, color: T.accent}}>{big}</div> : null}
      <Title title={title} accent={accent} size={big ? 110 : 124} />
      {logos.length ? (
        <div style={{display: 'flex', gap: 22, marginTop: 20}}>
          {logos.map((l) => <Img key={l} src={staticFile(l)} style={{width: 110, height: 110, borderRadius: 26}} />)}
        </div>
      ) : null}
    </div>
    {!image ? (
      <div style={{position: 'absolute', top: SAFE.bottom - 200, left: 0, right: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 22}}>
        <Img src={staticFile(LOGO)} style={{width: 72, height: 72, borderRadius: 18}} />
        <div style={{fontFamily: FONT_MONO, fontSize: 32, letterSpacing: 6, color: T.ink60}}>{BRAND.handle}</div>
      </div>
    ) : null}
    {showSafeZone ? (
      <>
        <div style={{position: 'absolute', left: 0, top: 0, width: W, height: SAFE.top, background: 'rgba(255,0,0,0.25)'}} />
        <div style={{position: 'absolute', left: 0, top: SAFE.bottom, width: W, bottom: 0, background: 'rgba(255,0,0,0.25)'}} />
      </>
    ) : null}
  </AbsoluteFill>
);

// One cover per sample composition.
export const COVERS: {id: string; props: CoverProps}[] = [
  {id: 'CoverTalkingHead', props: {kicker: '3 rules', title: 'Stop losing viewers in 2 seconds', accent: 'seconds', image: 'video/take-cover.png'}},
  {id: 'CoverListicle', props: {kicker: 'Save this', big: '5', title: 'edits that keep people watching', accent: 'watching'}},
  {id: 'CoverCounter', props: {kicker: 'One post', big: '6', title: 'apps. Make it one.', accent: 'one', logos: ['logos/editor.svg', 'logos/captions.svg', 'logos/thumbnails.svg', 'logos/scheduler.svg', 'logos/analytics.svg', 'logos/inbox.svg']}},
  {id: 'CoverGameParody', props: {kicker: 'Final round', big: 'K.O.', title: 'Me vs my inbox', accent: 'inbox'}},
];
