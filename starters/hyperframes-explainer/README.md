# HyperFrames faceless explainer

A starter for 9:16 faceless explainers. You write a short script, record or generate a voiceover, and `gen.py` builds a [HyperFrames](https://hyperframes.heygen.com) project where:

- the script appears word by word at the top, in time with the voice;
- one slam word per line lands huge in your accent colour;
- under each line an animated card explains it (a list ticking, bars racing, a number counting, a cursor clicking, a gauge swinging, a quote highlighting, a profile card);
- something changes on screen every 2 to 4 seconds, and every change is keyed to a spoken word;
- one sound track (whoosh, slam, tick, land and a few more) is written by the same code that places the motion, so every motion event has its cue.

Colours, fonts, name, handle, URL, logo and call to action come from the repo's `brand/brand.json`. `preview.jpg` shows the sample video in the default dark look (top) and the paper look (bottom).

## Files

| File | What it does |
| --- | --- |
| `gen.py` | Reads `script.json`, `words.json` and `brand.json`; writes the HyperFrames project into `hf/` and the sound track into `hf/assets/sfx-mix.wav` |
| `sfx.py` | Synthesizes the sound pack with numpy (no downloaded sound files). `gen.py` runs it when the pack is missing |
| `transcribe.py` | Word timestamps for a voiceover with faster-whisper |
| `looks.md` | The dark and paper looks, and how to match a reference's look |
| `script.json`, `vo.mp3`, `words.json` | The sample: "Three habits that make short videos easier", voiced locally with Kokoro |
| `fonts/` | Geist and Geist Mono (SIL Open Font License), used by the default brand kit |
| `hf/` | The generated HyperFrames project. Don't edit by hand; change the script or `gen.py` and re-run |

## Requirements

- Python 3.9 or newer with numpy (`pip install numpy`)
- Node.js 18 or newer, for `npx hyperframes`
- ffmpeg on your PATH
- For transcription: `pip install faster-whisper` (or run it with `uv run --with faster-whisper --with numpy`)

## Quick start

```bash
cd starters/hyperframes-explainer
python3 gen.py                         # build hf/ from the sample
cd hf
npx hyperframes check                  # lint, layout, contrast and timing checks
npx hyperframes preview                # open the preview in your browser
npx hyperframes render -o ../out/explainer.mp4
cd ..
bash ../../tools/loudnorm.sh out/explainer.mp4 out/explainer-14.mp4   # -14 LUFS for TikTok, Reels and Shorts
```

Try the other look with `python3 gen.py --look paper`.

### Your own video

1. Write `script.json` (schema below).
2. Make a voiceover that reads the lines exactly. Your own recording works best. For a free local voice:
   ```bash
   npx hyperframes tts "First line. Second line." -v am_michael -o vo.wav
   ffmpeg -i vo.wav -b:a 128k vo.mp3
   ```
   (On a Mac, `say -o vo.aiff "..."` also works as a fallback.)
3. Get word times: `python3 transcribe.py vo.mp3 words.json`
4. `python3 gen.py`, then check, preview and render as above.

## script.json

```json
{
  "title": "Three habits that make short videos easier",
  "audio": "vo.mp3",
  "words": "words.json",
  "look": "dark",
  "hold": 2.0,
  "scenes": [[0, 1], [2, 3], [4, 5], [6, 7]],
  "lines": [
    {
      "text": "Short videos get easier with three simple habits.",
      "slam": "three",
      "card": {"type": "counter", "from": 0, "to": 3, "label": "habits", "at": "habits."}
    }
  ]
}
```

| Key | Meaning |
| --- | --- |
| `audio`, `words` | Voiceover file and its word times, relative to the script |
| `look` | `dark` or `paper` (see `looks.md`); `--look` overrides it |
| `hold` | Seconds to hold the last card after the voice ends |
| `scenes` | Groups of line indexes, one sub-composition each. Defaults to pairs. The ground can change between scenes |
| `lines[].text` | Exactly what is spoken. Every token is matched to a whisper word |
| `lines[].slam` | The word (or words) from `text` that slam in big |
| `lines[].card` | The card under the line: a `type` plus its options |

Any `at` option names a word from that line's text (case and punctuation ignored); the motion lands on the moment it is spoken. Leave it out and the card spreads its beats across the line.

### Card types

| Type | Options | Motion and sound |
| --- | --- | --- |
| `list-ticks` | `title`, `items` (strings or `{"label", "at"}`), `allAt` | Rows light up and tick (tick); all rows glow on `allAt` (chime) |
| `bar-grow` | `title`, `bars` (`{"label", "value", "to"}`, values 0 to 1), `raceAt`, `tag` (`{"bar", "text", "at"}`) | Bars grow in (tick); on `raceAt` they move to `to` and swap rank (whoosh, land); the tag pops on (pop) |
| `counter` (or `odometer`) | `from`, `to`, `label`, `prefix`, `suffix`, `note`, `at` | Odometer rolls and lands on `at` (roll, land, chime) with a debris burst (rattle) |
| `cursor-click` | `title`, `button`, `done`, `at` | Cursor glides in and clicks on `at`; the label swaps (click, pop) |
| `gauge` | `label`, `from`, `to` (0 to 1), `value`, `color` (`accent`, `success`, `danger`), `low`, `high`, `at` | Needle swings and the arc recolours (ticks, land) |
| `quote` (or `highlight`) | `text`, `highlight` (words of the quote), `by`, `at` | Highlight boxes wipe in behind the words (tick, whoosh) |
| `cta-profile` | `button`, `done`, `sub`, `at` | Your logo, name, handle and URL from brand.json; the cursor clicks the button (click, chime) |

Slam words get the slam sound, other words a very quiet tick, and cards a whoosh or a land as they enter.

## Add a card type

1. Write a function in `gen.py` next to the others:
   ```python
   def card_checklist(sc, ln, o):
       g = sc.g                                   # colours of this scene's ground
       sc.card(ln, sc.panel("...markup with stable ids..."), top=760, height=500)
       t = sc.at(ln, o.get("at"), sc.window(ln)[0] + 0.8)   # spoken word, or a default
       sc.tw(f'tl.fromTo("#{sc.id}-c{ln}-x", {{scale:0}}, {{scale:1, duration:0.3}}, {t});')
       sc.cue(t, "pop", 0.5)                      # every motion event gets a sound
   ```
2. Register it in `CARDS` at the bottom of the card section.
3. Use it in `script.json` and re-run `gen.py`.

Rules from the HyperFrames contract: give every element a stable `id`, animate transforms and opacity rather than layout, no `Math.random()` (use `seeded()`), and take colours from `sc.g` and fonts from the look so the card works in every look.

## Lessons

- **Key every visible change to a spoken word.** Use `at` and `sc.find()`, never typed seconds. A change that lands off the voice feels wrong even when nobody can say why.
- **Re-run `gen.py` after any script or timing change.** New voiceover, edited line, swapped card: re-transcribe if the audio changed, then re-run. The timings in `hf/` are baked in.
- **Whisper splits and merges words.** It turns "step-by-step" into "step" "-by" "-step", "7pm" into one token where your script says "7 PM", and the sample's "Hook, point," came back as "Hookpoint". `load_words()` and `align()` glue these back; keep that code when you adapt the generator.
- **Put a cue on every motion event.** Writing the sound in the same function as the motion is what keeps them in sync. A card that moves silently feels unfinished.
- **Normalise to -14 LUFS** before posting. The raw render of the sample measures about -20 LUFS; `tools/loudnorm.sh` brings it to the platform target.
- **Frame 0 is the thumbnail.** The first line is already on screen at frame 0, so the video never opens on an empty frame.
- **Keep text inside the safe zone.** The headline starts just above `safeZone.top` and cards sit in the middle. Check snapshots at phone width with `npx hyperframes snapshot`.
- **Renders stay out of git.** `out/`, `*.mp4`, `hf/renders/` and `hf/.hyperframes/` are ignored.
