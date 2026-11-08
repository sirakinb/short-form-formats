import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import wordsJson from '../../public/words/game-parody.json';
import {Banner, Burst, Captions, Chore, During, EndCard, Fighter, Footer, Glyph, Hud, ProgressBar, SafeZoneGuide, Sfx, clamp, healthAt, useT} from '../kit';
import {BRAND, LOGO, T} from '../theme';
import {lastWord, loadWords, makeAt} from '../words';

// Game parody: your logo fights a chore, round by round, with health bars, hits and a K.O.
// Every hit lands on a spoken word from public/words/game-parody.json.

const words = loadWords(wordsJson, 'game-parody.json');
const at = makeAt(words, 'game-parody.json');
export const GAME_PARODY_END = lastWord(words).e + 1.6;

const FLOOR = 1250;
const HERO_X = 300;
const FOE_X = 790;
const B = {
  inbox: at('inbox'), round1: at('Round'), unread: at('unread'), final: at('Final'), ko: at('K.O.'), zero: at('zero'), follow: at('Follow'),
};
const HITS_1 = [at('Archive'), at('Filter'), at('Reply')];
const HITS_2 = [at('Unsubscribe'), B.ko];
const FALL_1 = HITS_1[2] + 0.35;
const ALL_HITS = [...HITS_1, ...HITS_2];

// How far the hero's arm is out: a quick jab around each hit.
const punchAt = (t: number) => Math.max(0, ...ALL_HITS.map((h) => interpolate(t, [h - 0.15, h, h + 0.3], [0, 1, 0], clamp)));

const Arena: React.FC = () => {
  const t = useT();
  const round2 = t >= B.final;
  const won = t >= B.ko + 0.4;
  const unread = ['200 UNREAD', '120 UNREAD', '45 UNREAD', '0 UNREAD'][HITS_1.filter((h) => t >= h).length];
  const foe = won ? 'K.O.' : round2 ? 'NEWSLETTERS' : 'INBOX';
  const health = round2 ? healthAt(t, HITS_2) : healthAt(t, HITS_1);
  const punch = punchAt(t);
  return (
    <>
      <Hud hero={BRAND.name.toUpperCase()} foe={foe} health={health} />
      <div style={{position: 'absolute', left: 0, right: 0, top: FLOOR, height: 2, background: T.line}} />
      <Fighter src={LOGO} x={HERO_X + punch * 140 + (won ? 140 : 0)} floor={FLOOR} punch={punch} cheer={won} />
      {!round2 ? <Chore label={unread} glyph={Glyph.inbox()} x={FOE_X} floor={FLOOR} enter={B.inbox} hits={HITS_1} ko={FALL_1} /> : null}
      {round2 ? <Chore label="NEWSLETTER PILE" glyph={Glyph.doc()} x={FOE_X} floor={FLOOR} enter={B.final} hits={HITS_2} ko={B.ko + 0.1} color={T.danger} /> : null}
      {ALL_HITS.map((h) => <Burst key={h} x={FOE_X - 110} y={FLOOR - 260} at={h} />)}
    </>
  );
};

export const GameParody: React.FC<{showSafeZone?: boolean}> = ({showSafeZone = false}) => (
  <AbsoluteFill style={{background: T.bg}}>
    <During from={0} to={B.follow}>
      <Arena />
      <Banner text="ME VS MY INBOX" from={0} to={B.round1 - 0.05} top={480} size={110} />
      <Banner text="ROUND 1" from={B.round1} to={B.unread + 0.5} top={480} color={T.accent} />
      <Banner text="FINAL ROUND" from={B.final} to={B.final + 1.6} top={480} color={T.accent} />
      <Banner text="K.O." from={B.ko} to={B.zero - 0.1} top={460} size={200} color={T.accent} />
      <Banner text="INBOX ZERO" from={B.zero - 0.1} to={B.follow} top={480} size={130} color={T.success} />
    </During>
    <During from={B.follow} to={GAME_PARODY_END}><EndCard at={B.follow} cta="Follow for more" /></During>

    <ProgressBar />
    <During from={0} to={B.follow}><Footer /></During>
    <Captions words={words} top={1400} size={84} accentWords={['inbox', 'unread', 'k.o', 'zero']} hideAfter={B.follow - 0.05} />

    <Sfx name="whoosh" at={0} volume={0.3} />
    <Sfx name="slam" at={B.inbox} volume={0.3} />
    {[B.round1, B.final].map((t) => <Sfx key={t} name="slam" at={t} volume={0.35} />)}
    {ALL_HITS.map((t) => <Sfx key={t} name="hit" at={t} volume={0.45} />)}
    <Sfx name="slam" at={B.ko} volume={0.5} />
    <Sfx name="pop" at={B.zero} volume={0.4} />
    {showSafeZone ? <SafeZoneGuide /> : null}
  </AbsoluteFill>
);
