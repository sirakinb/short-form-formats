import React from 'react';
import {Img, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {T, W, s} from '../theme';

// Logos orbiting a centre piece; they fly out one by one from `at` and keep turning slowly.
// `logos` are paths inside public/ (use the real logos of the tools you mention).
export const Orbit: React.FC<{center: React.ReactNode; logos: string[]; at: number; top: number; r?: number; size?: number; stagger?: number}> = ({
  center, logos, at, top, r = 330, size = 120, stagger = 0.09,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const spin = Math.max(0, frame - s(at)) * 0.5;
  return (
    <div style={{position: 'absolute', top, left: 0, width: W, height: r * 2 + size}}>
      <div style={{position: 'absolute', left: W / 2 - r, top: size / 2, width: r * 2, height: r * 2, borderRadius: '50%', border: `2px dashed ${T.ink30}`}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: size / 2 + r, transform: 'translateY(-50%)', display: 'flex', justifyContent: 'center'}}>{center}</div>
      {logos.map((src, i) => {
        const p = spring({frame: frame - s(at + i * stagger), fps, config: {damping: 11, stiffness: 220}});
        const a = ((spin + (i * 360) / logos.length - 90) * Math.PI) / 180;
        return (
          <Img key={src + i} src={staticFile(src)} style={{position: 'absolute', width: size, height: size, borderRadius: size * 0.23,
            left: W / 2 + Math.cos(a) * r * p - size / 2, top: size / 2 + r + Math.sin(a) * r * p - size / 2, transform: `scale(${p})`, opacity: p > 0.01 ? 1 : 0}} />
        );
      })}
    </div>
  );
};
