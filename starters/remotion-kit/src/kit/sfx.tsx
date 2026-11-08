import React from 'react';
import {Audio, Sequence, staticFile} from 'remotion';
import {s} from '../theme';

// Sound effects live in public/sfx (synthesized by scripts/make-assets.py; swap in your own).
export type SfxName = 'tick1' | 'tick2' | 'tick3' | 'whoosh' | 'slam' | 'hit' | 'pop';

// One sound at `at` seconds.
export const Sfx: React.FC<{name: SfxName; at: number; volume?: number}> = ({name, at, volume = 0.4}) => (
  <Sequence from={Math.max(0, s(at))} durationInFrames={s(1.5)} layout="none">
    <Audio src={staticFile(`sfx/${name}.wav`)} volume={volume} />
  </Sequence>
);

// A quiet tick on every cut, rotating through three pitches so it never sounds like a metronome.
// Pass `slams` for the cuts that should hit harder (full-screen graphics, big reveals).
export const CutTicks: React.FC<{at: number[]; slams?: number[]; volume?: number; slamVolume?: number}> = ({at, slams = [], volume = 0.25, slamVolume = 0.35}) => (
  <>
    {at.map((t, k) => (slams.includes(t)
      ? <Sfx key={`c${k}`} name="slam" at={t} volume={slamVolume} />
      : <Sfx key={`c${k}`} name={(['tick1', 'tick2', 'tick3'] as const)[k % 3]} at={t} volume={volume} />))}
  </>
);
