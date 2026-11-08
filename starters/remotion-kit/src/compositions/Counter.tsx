import React from 'react';
import {AbsoluteFill, Img, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import wordsJson from '../../public/words/counter.json';
import {Captions, Check, During, EndCard, Footer, Label, Orbit, ProgressBar, SafeZoneGuide, Sfx, Slam, StatLine, StepCounter} from '../kit';
import {FONT_HEAD, FONT_MONO, LOGO, SAFE, T, s} from '../theme';
import {lastWord, loadWords, makeAt, makeEnd} from '../words';

// Counter: a number climbs as each item is named, then the payoff lands as three stat lines.
// Swap ITEMS for your own list and use real logos in public/logos.

const words = loadWords(wordsJson, 'counter.json');
const at = makeAt(words, 'counter.json');
const end = makeEnd(words, 'counter.json');
export const COUNTER_END = lastWord(words).e + 1.6;

const ITEMS: {word: string; name: string; note: string; logo: string}[] = [
  {word: 'Editor', name: 'Editor', note: 'CUT THE TAKE', logo: 'logos/editor.svg'},
  {word: 'Captions', name: 'Captions', note: 'BURN IN THE WORDS', logo: 'logos/captions.svg'},
  {word: 'Thumbnails', name: 'Thumbnails', note: 'MAKE THE COVER', logo: 'logos/thumbnails.svg'},
  {word: 'Scheduler', name: 'Scheduler', note: 'PICK THE TIME', logo: 'logos/scheduler.svg'},
  {word: 'Analytics', name: 'Analytics', note: 'READ THE NUMBERS', logo: 'logos/analytics.svg'},
  {word: 'Inbox', name: 'Inbox', note: 'ANSWER COMMENTS', logo: 'logos/inbox.svg'},
];
const ROW_AT = ITEMS.map((it) => at(it.word));
const TICK_AT = ITEMS.map((it) => end(it.word));
const B = {
  how: at('How'), count: at('count'), now: at('Now'), put: at('put'), six2: at('Six', 2), one2: at('one', 3), zero: at('Zero'), follow: at('Follow'),
};

const Row: React.FC<{name: string; note: string; logo: string; at: number; tickAt: number}> = ({name, note, logo, at: t0, tickAt}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - s(t0), fps, config: {damping: 13, stiffness: 240}});
  const tick = spring({frame: frame - s(tickAt), fps, config: {damping: 9, stiffness: 300}});
  if (frame < s(t0)) return <div style={{height: 104}} />;
  return (
    <div style={{height: 104, display: 'flex', alignItems: 'center', gap: 22, padding: '0 22px', border: `1px solid ${tick > 0.5 ? T.accentFaint : T.line}`, background: T.card, borderRadius: 18,
      transform: `translateX(${(1 - p) * 900}px)`}}>
      <Img src={staticFile(logo)} style={{width: 70, height: 70, borderRadius: 16}} />
      <div style={{flex: 1}}>
        <div style={{fontFamily: FONT_HEAD, fontWeight: 700, fontSize: 40, color: T.ink}}>{name}</div>
        <div style={{fontFamily: FONT_MONO, fontSize: 20, letterSpacing: 3, color: T.muted}}>{note}</div>
      </div>
      <div style={{width: 58, height: 58, borderRadius: 29, background: T.success, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${tick})`}}>
        <Check size={38} color={T.bg} />
      </div>
    </div>
  );
};

export const Counter: React.FC<{showSafeZone?: boolean}> = ({showSafeZone = false}) => (
  <AbsoluteFill style={{background: T.bg}}>
    <During from={0} to={B.count}>
      <Label text="ONE POST" at={B.how} top={420} size={40} />
      <Slam text="How many apps?" at={B.how + 0.2} top={520} size={150} />
      <Label text="LET'S COUNT" at={at("Let's")} top={900} size={40} color={T.accent} />
    </During>

    <During from={B.count} to={B.now}>
      <StepCounter steps={ROW_AT} top={SAFE.top + 20} size={220} unit={['APP', 'APPS']} />
      <div style={{position: 'absolute', top: 600, left: 50, right: 50, display: 'flex', flexDirection: 'column', gap: 10}}>
        {ITEMS.map((it, i) => <Row key={it.word} {...it} at={ROW_AT[i]} tickAt={TICK_AT[i]} />)}
      </div>
    </During>

    <During from={B.now} to={B.six2}>
      <Label text="ALL IN ONE PLACE" at={B.now} top={SAFE.top + 40} size={40} />
      <Orbit at={B.put} top={420} r={330} logos={ITEMS.map((it) => it.logo)}
        center={<Img src={staticFile(LOGO)} style={{width: 220, height: 220, borderRadius: 50}} />} />
    </During>

    <During from={B.six2} to={B.follow}>
      <StatLine n="6" label="APPS" at={B.six2} top={360} />
      <StatLine n="1" label="PLACE" at={B.one2} top={680} />
      <StatLine n="0" label="TABS" at={B.zero} top={1000} color={T.accent} />
    </During>

    <During from={B.follow} to={COUNTER_END}><EndCard at={B.follow} /></During>

    <ProgressBar />
    <During from={0} to={B.follow}><Footer /></During>
    <Captions words={words} top={1440} size={80} accentWords={['count', 'six', 'one', 'zero']} hideAfter={B.follow - 0.05} />

    <Sfx name="whoosh" at={0} volume={0.3} />
    <Sfx name="slam" at={B.count} volume={0.3} />
    {ROW_AT.map((t) => <Sfx key={t} name="tick1" at={t} volume={0.3} />)}
    {TICK_AT.map((t) => <Sfx key={t} name="pop" at={t} volume={0.25} />)}
    <Sfx name="whoosh" at={B.put} volume={0.3} />
    {[B.six2, B.one2, B.zero].map((t) => <Sfx key={t} name="slam" at={t} volume={0.35} />)}
    <Sfx name="slam" at={B.follow} volume={0.3} />
    {showSafeZone ? <SafeZoneGuide /> : null}
  </AbsoluteFill>
);
