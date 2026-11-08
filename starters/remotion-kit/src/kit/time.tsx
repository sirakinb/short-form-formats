import React from 'react';
import {Easing, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {s} from '../theme';

// Every `at`, `from` and `to` in the kit is in seconds on the composition timeline.

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const ease = Easing.bezier(0.45, 0, 0.2, 1);
export const easeOut = (x: number) => 1 - Math.pow(1 - x, 3);

// Current time in seconds.
export const useT = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return frame / fps;
};

// 0 before `at`, springs to 1 after. Lower damping = more bounce.
export const usePop = (at: number, damping = 12, stiffness = 220) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - s(at), fps, config: {damping, stiffness}});
};

// Render children only while from <= t < to.
export const During: React.FC<{from: number; to: number; children: React.ReactNode}> = ({from, to, children}) => {
  const t = useT();
  return t >= from && t < to ? <>{children}</> : null;
};

// Throw if a list of beat times is not strictly increasing. Catches a cue keyed to the wrong word.
export const assertOrdered = (times: number[], name = 'beats') => {
  times.forEach((t, k) => {
    if (k && t <= times[k - 1]) throw new Error(`${name}[${k}] (${t.toFixed(2)}s) is not after ${name}[${k - 1}] (${times[k - 1].toFixed(2)}s)`);
  });
};

// Index of the last time in `times` that has started (0 if none).
export const indexAt = (times: number[], t: number) => {
  let i = 0;
  for (let k = 0; k < times.length; k++) if (t >= times[k]) i = k;
  return i;
};
