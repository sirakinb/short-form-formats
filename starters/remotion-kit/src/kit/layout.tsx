import React from 'react';
import {OffthreadVideo, Sequence, staticFile} from 'remotion';
import {H, W, s} from '../theme';
import {Edit, Word} from '../words';
import {assertOrdered, indexAt, useT} from './time';

// Talking-head layout modes, switched beat by beat on spoken words:
//   face  - the take fills the frame (every other face beat punches in 15%)
//   split - a graphic on top, the take below, joined by a soft seam
//   full  - the graphic fills the frame; the take keeps playing underneath for sound

export type Mode = 'face' | 'split' | 'full';
export type BeatProps = {start: number; end: number; h: number};
export type Beat = {t: number; mode: Mode; punch?: boolean; render?: (b: BeatProps) => React.ReactNode};

export const SPLIT_H = 960;
const SEAM_FADE = 140;

// Throws if beats are out of order (usually a cue keyed to the wrong occurrence of a word).
export const checkBeats = (beats: Beat[]) => assertOrdered(beats.map((b) => b.t), 'beat');

export const useBeat = (beats: Beat[]) => {
  const t = useT();
  const i = indexAt(beats.map((b) => b.t), t);
  return {i, beat: beats[i]};
};

// Where captions should sit for the current mode: on the seam in split, low in face and full.
export const captionTopFor = (mode: Mode) => (mode === 'split' ? SPLIT_H - 40 : 1400);

// An edit that keeps the whole take, for footage you have already trimmed.
export const straightEdit = (words: Word[], duration: number): Edit => ({duration, segments: [{from: 0, to: duration, at: 0}], words});

// The take, played back segment by segment so the silences cut out by tools/cuts.py are skipped.
const Take: React.FC<{beats: Beat[]; edit: Edit; video: string; faceY: string}> = ({beats, edit, video, faceY}) => {
  const {i, beat} = useBeat(beats);
  const split = beat.mode === 'split';
  const faceIndex = beats.slice(0, i + 1).filter((b) => b.mode === 'face').length;
  const punch = beat.mode === 'face' && (beat.punch ?? faceIndex % 2 === 0) ? 1.15 : 1;
  return (
    <div style={{position: 'absolute', left: 0, width: W, top: split ? SPLIT_H - SEAM_FADE : 0, bottom: 0, overflow: 'hidden'}}>
      {edit.segments.map((seg, k) => (
        <Sequence key={k} from={s(seg.at)} durationInFrames={Math.max(1, s(seg.to - seg.from))} layout="none">
          <OffthreadVideo src={staticFile(video)} startFrom={s(seg.from)} endAt={s(seg.to) + 1}
            style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: `center ${split ? faceY : '50%'}`, transform: `scale(${punch})`, transformOrigin: 'center 35%'}} />
        </Sequence>
      ))}
    </div>
  );
};

const Graphic: React.FC<{beats: Beat[]; end: number}> = ({beats, end}) => {
  const {i, beat} = useBeat(beats);
  if (beat.mode === 'face' || !beat.render) return null;
  const h = beat.mode === 'split' ? SPLIT_H : H;
  const mask = beat.mode === 'split' ? `linear-gradient(to bottom, black ${((SPLIT_H - SEAM_FADE) / SPLIT_H) * 100}%, transparent 100%)` : undefined;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: W, height: h, overflow: 'hidden', WebkitMaskImage: mask, maskImage: mask}}>
      {beat.render({start: beat.t, end: beats[i + 1]?.t ?? end, h})}
    </div>
  );
};

// The take plus whatever graphic the current beat renders. `faceY` sets the vertical crop of the
// face in split mode (lower percentage = higher in the frame).
export const ModeEdit: React.FC<{beats: Beat[]; edit: Edit; video: string; end: number; faceY?: string}> = ({beats, edit, video, end, faceY = '32%'}) => (
  <>
    <Take beats={beats} edit={edit} video={video} faceY={faceY} />
    <Graphic beats={beats} end={end} />
  </>
);
