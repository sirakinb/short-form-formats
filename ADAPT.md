# Make it yours

This kit came out of one creator's workflow. Here is how to turn it into yours in about an hour.

## 1. Fill in your brand kit (10 minutes)
Open `brand/brand.json` and change:
- `name`, `handle`, `url`: shown on end cards, covers and carousel footers.
- `colors`: keep the roles (background, card, line, text, muted, one accent, success, danger). Dark or light both work.
- `fonts`: a heavy headline font and a label font, with a Google Fonts URL.
- `logo`: replace `brand/logo.svg` with yours.
- `voice`: your ElevenLabs voice ID if you use a clone or narrator.
- `cta`: what your end cards say ("Link in bio", "Free to try").
- `banned`: phrases you never want in a script.

## 2. Render one sample from each starter (20 minutes)
Follow the quick start in each `starters/*/README.md`. Put the results side by side. If something looks off-brand, fix `brand.json` first, then the starter, so the fix applies everywhere.

## 3. Pick your two or three formats (5 minutes)
You don't need all ten. A common set:
- **Personal brand:** talking head + news carousel.
- **Product or startup:** game parody or animated explainer + news carousel.
- **Faceless account:** faceless explainer + reference remakes + carousels.

Delete or ignore the rest.

## 4. Change the rules to match how you work
- **Pace:** the guides assume dense edits (a new visual every 1–2 s). If your audience likes calmer videos, change the numbers in `shared/motion-language.md`.
- **Platforms:** the guides say carousels on TikTok and reels on Instagram, because that's what our numbers showed. Track yours (`shared/testing-and-stats.md`) and rewrite the line.
- **Voice and tone:** add your own banned phrases, hook styles and CTA wording to `shared/script-and-captions.md`.
- **Tools:** each format names the tool we used. If you prefer CapCut, After Effects or Premiere, keep the format guide (structure, pacing, sound) and skip the starter.

## 5. Add your own format
When a new piece works, make it repeatable:
1. Copy any file in `formats/` to `formats/<your-format>.md` and fill in: what it is, use it when, built with, steps, lessons.
2. Make a frame strip of the finished video: `tools/make_strip.sh final.mp4 examples/<your-format>/frames.jpg 6`.
3. Add a row to the format table in `SKILL.md` and `README.md`.

## 6. Use it with an AI assistant (optional)
The repo is also a Claude Code skill. Clone it into your skills folder:
```bash
git clone <repo-url> ~/.claude/skills/short-form-formats
```
Then ask for "a talking head about X" or "remake this reel: <link>". The assistant reads `SKILL.md`, your `brand.json` and the format guide, and builds from the starters.
