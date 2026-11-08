import React from 'react';
import {AbsoluteFill} from 'remotion';
import editJson from '../../public/words/talking-head.edit.json';
import {
  Beat, BigWord, Captions, CountUp, CutTicks, EndCard, ModeEdit, PANEL_W, Panel, ProgressBar, SafeZoneGuide, Shot, Tag, WordStack, captionTopFor, checkBeats, useBeat,
} from '../kit';
import {LOGO, T} from '../theme';
import {lastWord, loadEdit, makeAt} from '../words';
import {SafeZoneDiagram} from './demo-graphics';

// Talking head: the layout switches on spoken words between face, split and full-screen graphics.
// The take is public/video/take.mp4; its words and silence cuts are public/words/talking-head.edit.json
// (made by tools/transcribe.py then tools/cuts.py). Edit BEATS below to make your own.

const edit = loadEdit(editJson, 'talking-head.edit.json');
const at = makeAt(edit.words, 'talking-head.edit.json');
const LAST = lastWord(edit.words).e;
const OUTRO = LAST + 0.25;
export const TALKING_HEAD_END = OUTRO + 2.4;

// Rectangles on public/shots/sample-ui.png (2160x1350) for camera moves and marks.
const SHOT = {src: 'shots/sample-ui.png', natW: 2160};
const R = {
  all: [0, 0, 2160, 1350] as const,
  chart: [400, 450, 1200, 570] as const,
  stat: [1000, 160, 600, 280] as const,
  statCard: [1020, 180, 560, 240] as const,
  tip: [420, 1050, 1700, 240] as const,
};
const rect = (r: readonly number[]) => [...r] as [number, number, number, number];
const PANEL = {top: 380, height: 430}; // sits between the tag and the seam

const BEATS: Beat[] = [
  {t: 0, mode: 'face'},
  {t: at('lose'), mode: 'split', render: () => (
    <>
      <Tag text="THE FIRST 2 SECONDS" at={at('lose')} />
      <CountUp from={2} to={0} at={at('two')} dur={1.6} decimals={1} suffix="s" top={400} size={300} sub="BEFORE THEY SCROLL" color={T.accent} />
    </>
  )},
  {t: at('fix'), mode: 'full', render: ({start}) => <BigWord text="THE FIX" at={start} icon={LOGO} sub="3 RULES" size={200} />},
  {t: at('Change'), mode: 'split', render: ({start, end}) => (
    <>
      <Tag text="NEW VISUAL EVERY 1-2 S" at={start} />
      <Panel top={PANEL.top} height={PANEL.height} at={start}>
        <Shot {...SHOT} from={rect(R.all)} to={rect(R.chart)} start={start} end={end} boxH={PANEL.height} boxW={PANEL_W} marks={[{rect: rect(R.tip), at: at('picture')}]} />
      </Panel>
    </>
  )},
  {t: at('one'), mode: 'face'},
  {t: at('Show'), mode: 'split', render: ({start, end}) => (
    <>
      <Tag text="REAL UI, NOT A REDRAW" at={start} />
      <Panel top={PANEL.top} height={PANEL.height} at={start}>
        <Shot {...SHOT} from={rect(R.all)} to={rect(R.stat)} start={start} end={end - 0.3} boxH={PANEL.height} marks={[{rect: rect(R.statCard), at: at('real')}]} />
      </Panel>
    </>
  )},
  {t: at('not'), mode: 'face'},
  {t: at('Keep'), mode: 'split', render: ({start}) => (
    <>
      <Tag text="THE SAFE ZONE" at={start} />
      <SafeZoneDiagram at={start} bandsAt={at('safe')} top={350} height={460} />
    </>
  )},
  {t: at('Three'), mode: 'full', render: () => (
    <WordStack items={[
      {text: 'Move fast', at: at('move')},
      {text: 'Real screens', at: at('show', 2)},
      {text: 'Safe zone', at: at('stay')},
    ]} />
  )},
  {t: at('Follow'), mode: 'face'},
  {t: OUTRO, mode: 'full', render: ({start}) => <EndCard at={start} />},
];
checkBeats(BEATS);

const LiveCaptions: React.FC = () => {
  const {beat} = useBeat(BEATS);
  if (beat.mode === 'full') return null;
  return <Captions words={edit.words} top={captionTopFor(beat.mode)} size={beat.mode === 'split' ? 68 : 84} look="box" accentWords={['seconds', 'fix', 'real', 'safe']} hideAfter={LAST + 0.2} />;
};

export const TalkingHead: React.FC<{showSafeZone?: boolean}> = ({showSafeZone = false}) => (
  <AbsoluteFill style={{background: T.bg}}>
    <ModeEdit beats={BEATS} edit={edit} video="video/take.mp4" end={TALKING_HEAD_END} />
    <LiveCaptions />
    <ProgressBar />
    <CutTicks at={BEATS.slice(1).map((b) => b.t)} slams={BEATS.filter((b) => b.mode === 'full').map((b) => b.t)} />
    {showSafeZone ? <SafeZoneGuide /> : null}
  </AbsoluteFill>
);
