// Renders a few frames of every composition plus each cover and tiles them into preview.jpg.
// Usage: npm run preview   (needs ffmpeg on your PATH)
// Look at the sheet before you publish anything: text near the top or bottom edge, a graphic
// cut off mid-animation, or two beats that look the same all show up here.
import {execFileSync} from 'node:child_process';
import {mkdirSync, rmSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {getCompositions, renderStill} from '@remotion/renderer';

const kit = resolve(dirname(fileURLToPath(import.meta.url)), '..');
execFileSync('node', [join(kit, 'scripts/sync-brand.mjs')], {stdio: 'inherit'});
const frames = join(kit, 'out/preview-frames');
rmSync(frames, {recursive: true, force: true});
mkdirSync(frames, {recursive: true});

const serveUrl = await bundle({entryPoint: join(kit, 'src/index.ts')});
const comps = await getCompositions(serveUrl);
// Seconds to sample in each video. Pick moments that show each beat type.
const PICKS = {
  TalkingHead: [0.6, 2.9, 5.4, 6.8, 10.8, 14.6, 19.5, 23.6],
  Listicle: [1.6, 4.2, 6.4, 10.9, 14.0, 17.9, 19.7],
  Counter: [1.4, 7.6, 9.9, 12.4, 15.5, 18.5],
  GameParody: [1.0, 2.5, 5.0, 7.7, 11.6, 12.8],
};
let n = 0;
for (const c of comps) {
  const times = c.durationInFrames === 1 ? [0] : PICKS[c.id] ?? [c.durationInFrames / c.fps / 2];
  for (const t of times) {
    const frame = Math.min(c.durationInFrames - 1, Math.round(t * c.fps));
    const out = join(frames, `${String(n++).padStart(2, '0')}-${c.id}-${frame}.png`);
    await renderStill({composition: c, serveUrl, output: out, frame, scale: 0.25});
    console.log(out.replace(kit + '/', ''));
  }
}
const cols = 8;
const rows = Math.ceil(n / cols);
execFileSync('ffmpeg', ['-v', 'error', '-y', '-pattern_type', 'glob', '-i', join(frames, '*.png'),
  '-vf', `scale=270:480,pad=iw+6:ih+6:3:3:color=0x333333,tile=${cols}x${rows}:color=0x111111`, '-frames:v', '1', '-q:v', '3', join(kit, 'preview.jpg')], {stdio: 'inherit'});
console.log(`preview.jpg: ${n} frames`);
