import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import wordsJson from '../../public/words/listicle.json';
import {
  Captions, During, EndCard, Footer, Label, PANEL_W, Panel, ProgressBar, Rect, SafeZoneGuide, Sfx, Shot, Slam, StepDots, StepHeader, indexAt, useCamera, useT,
} from '../kit';
import {LOGO, T} from '../theme';
import {lastWord, loadWords, makeAt} from '../words';
import {CaptionDemo, PauseCut, SafeZoneDiagram} from './demo-graphics';

// Listicle: "5 edits that keep people watching". A numbered step per item, each shown on a real screen.
// Narration timing comes from public/words/listicle.json. Drop your voiceover in public/audio and
// pass it as the `audio` prop (or add an <Audio>) once you have recorded it.

const words = loadWords(wordsJson, 'listicle.json');
const at = makeAt(words, 'listicle.json');
export const LISTICLE_END = lastWord(words).e + 1.6;

const B = {
  five: at('Five'), keep: at('keep'), s1: at('One'), pause: at('pause'), s2: at('Two'), picture: at('picture'), every: at('every', 2), seconds: at('seconds'),
  s3: at('Three'), real: at('real'), s4: at('Four'), accent: at('accent'), s5: at('Five', 2), safe: at('safe'), save: at('Save'),
};
const STEPS = [B.s1, B.s2, B.s3, B.s4, B.s5];
const PANEL = {top: 560, height: 760};
const SHOT = 'shots/sample-ui.png';

// Hard cuts between framings of the same screenshot, each with a slow push: a new picture on every cue.
const QuickCuts: React.FC<{cues: number[]; rects: Rect[]; end: number}> = ({cues, rects, end}) => {
  const t = useT();
  const i = indexAt(cues, t);
  const r = rects[i];
  const next = cues[i + 1] ?? end;
  const push: Rect = [r[0] + r[2] * 0.04, r[1] + r[3] * 0.04, r[2] * 0.92, r[3] * 0.92];
  const c = useCamera(r, push, cues[i], next, PANEL_W, PANEL.height);
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 2160, transform: `translate(${c.tx}px, ${c.ty}px) scale(${c.scale})`, transformOrigin: '0 0'}}>
      <Img src={staticFile(SHOT)} style={{width: 2160, display: 'block'}} />
    </div>
  );
};

export const Listicle: React.FC<{showSafeZone?: boolean}> = ({showSafeZone = false}) => (
  <AbsoluteFill style={{background: T.bg}}>
    <During from={0} to={B.save}><StepDots at={STEPS} /></During>

    <During from={0} to={B.s1}>
      <div style={{position: 'absolute', top: 360, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
        <Img src={staticFile(LOGO)} style={{width: 160, height: 160, borderRadius: 36}} />
      </div>
      <Slam text="5 edits" at={B.five} top={600} size={260} color={T.accent} />
      <Label text="THAT KEEP PEOPLE WATCHING" at={B.keep} top={900} size={40} />
    </During>

    <During from={B.s1} to={B.s2}>
      <StepHeader n={1} title="Cut every pause" at={B.s1} />
      <PauseCut at={B.s1 + 0.2} cutAt={B.pause} top={760} />
    </During>

    <During from={B.s2} to={B.s3}>
      <StepHeader n={2} title="New picture every 2 seconds" at={B.s2} />
      <Panel top={PANEL.top} height={PANEL.height} at={B.s2 + 0.15}>
        <QuickCuts cues={[B.s2, B.picture, B.every, B.seconds]} end={B.s3}
          rects={[[0, 0, 2160, 1350], [400, 450, 1200, 570], [1600, 450, 540, 570], [400, 160, 1220, 280]]} />
      </Panel>
    </During>

    <During from={B.s3} to={B.s4}>
      <StepHeader n={3} title="Show the real screen" at={B.s3} />
      <Panel top={PANEL.top} height={PANEL.height} at={B.s3 + 0.15}>
        <Shot src={SHOT} natW={2160} from={[0, 0, 2160, 1350]} to={[980, 140, 700, 480]} start={B.s3 + 0.15} end={B.s4 - 0.3} boxH={PANEL.height}
          marks={[{rect: [1020, 180, 560, 240], at: B.real}]} />
      </Panel>
    </During>

    <During from={B.s4} to={B.s5}>
      <StepHeader n={4} title="One accent word per caption" at={B.s4} />
      <CaptionDemo at={B.s4 + 0.2} accentAt={B.accent} top={800} />
    </During>

    <During from={B.s5} to={B.save}>
      <StepHeader n={5} title="Keep it in the safe zone" at={B.s5} />
      <SafeZoneDiagram at={B.s5 + 0.2} bandsAt={B.safe} top={600} height={700} />
    </During>

    <During from={B.save} to={LISTICLE_END}><EndCard at={B.save} cta="Save this" /></During>

    <ProgressBar />
    <During from={0} to={B.save}><Footer /></During>
    <Captions words={words} top={1420} size={80} accentWords={['5', 'five', 'pause', 'picture', 'real', 'accent', 'safe']} hideAfter={B.save - 0.05} />

    <Sfx name="whoosh" at={0} volume={0.3} />
    <Sfx name="slam" at={B.five} volume={0.35} />
    {STEPS.map((t) => <Sfx key={t} name="slam" at={t} volume={0.3} />)}
    {[B.picture, B.every, B.seconds].map((t) => <Sfx key={t} name="tick2" at={t} volume={0.25} />)}
    <Sfx name="pop" at={B.pause} volume={0.35} />
    <Sfx name="pop" at={B.real} volume={0.35} />
    <Sfx name="pop" at={B.accent} volume={0.35} />
    <Sfx name="pop" at={B.safe} volume={0.35} />
    <Sfx name="slam" at={B.save} volume={0.35} />
    {showSafeZone ? <SafeZoneGuide /> : null}
  </AbsoluteFill>
);
