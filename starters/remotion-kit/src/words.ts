// Word timing. Every beat in every composition starts on a spoken word, never on a hand-typed time,
// so when the take is re-cut or the voiceover is re-recorded the visuals stay in sync.
//
// Word lists come from tools/transcribe.py (faster-whisper): [{"w": "Hello", "s": 0.0, "e": 0.32}, ...]
// A talking-head edit comes from tools/cuts.py: {"duration", "segments", "words"}.

export type Word = {w: string; s: number; e: number};
export type Segment = {from: number; to: number; at: number};
export type Edit = {duration: number; segments: Segment[]; words: Word[]};

const isWord = (x: unknown): x is Word =>
  !!x && typeof (x as Word).w === 'string' && typeof (x as Word).s === 'number' && typeof (x as Word).e === 'number';

// Check a parsed JSON word list and return it typed. Throws with the index of the first bad entry.
export const loadWords = (json: unknown, name = 'words'): Word[] => {
  if (!Array.isArray(json)) throw new Error(`${name}: expected an array of {w, s, e}`);
  json.forEach((x, i) => {
    if (!isWord(x)) throw new Error(`${name}[${i}] is not {w: string, s: number, e: number}`);
  });
  return json as Word[];
};

// Check a parsed edit.json (from tools/cuts.py) and return it typed.
export const loadEdit = (json: unknown, name = 'edit'): Edit => {
  const e = json as Edit;
  if (!e || typeof e.duration !== 'number' || !Array.isArray(e.segments)) throw new Error(`${name}: expected {duration, segments, words}`);
  return {duration: e.duration, segments: e.segments, words: loadWords(e.words, `${name}.words`)};
};

// Lowercase, drop punctuation, keep inner dots so "5.5" and "K.O." still match.
export const norm = (x: string) => x.toLowerCase().replace(/[^a-z0-9.]/g, '').replace(/\.+$/, '');

// makeAt(words) returns at(word, nth): the start time in seconds of the nth time `word` is spoken.
// A word that is missing, or said fewer than nth times, throws, so a bad cue stops the render
// instead of quietly drifting out of sync.
export const makeAt = (words: Word[], name = 'words') => (word: string, nth = 1): number => {
  const hits = words.filter((w) => norm(w.w) === norm(word));
  const hit = hits[nth - 1];
  if (!hit) {
    const found = hits.length ? `it is only said ${hits.length} time(s)` : 'it is never said';
    throw new Error(`at("${word}", ${nth}): ${found} in ${name}`);
  }
  return hit.s;
};

// End time of the nth occurrence, for things that should land as a word finishes.
export const makeEnd = (words: Word[], name = 'words') => (word: string, nth = 1): number => {
  const start = makeAt(words, name)(word, nth);
  return words.find((w) => w.s === start && norm(w.w) === norm(word))!.e;
};

export const lastWord = (words: Word[]) => words[words.length - 1];

// Caption chunks: up to `maxWords` words or about `maxChars` characters, breaking after punctuation.
export const chunkWords = (words: Word[], maxWords = 3, maxChars = 17): Word[][] => {
  const out: Word[][] = [[]];
  for (const w of words) {
    const cur = out[out.length - 1];
    cur.push(w);
    const chars = cur.reduce((n, x) => n + x.w.length + 1, 0);
    if (cur.length >= maxWords || chars > maxChars || /[.,?!:;]$/.test(w.w)) out.push([]);
  }
  return out.filter((c) => c.length);
};
