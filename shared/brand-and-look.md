# Brand and look

All starters read `brand/brand.json`. Change it once and every format follows.

## The default look (pentridge-dark)
- **Colours:** black background `#000000`, cards `#0a0a0a`, borders `#262626`, text `#fafafa`, one accent (purple `#a855f7`, strong `#9333ea`, soft `#c084fc`). Green `#3dbb72` only for "done" ticks, red `#ef4444` only for errors or enemies.
- **Type:** Geist 800 with tight letter-spacing for headlines; Geist Mono in caps with wide letter-spacing for labels.
- **One accent:** besides black and white, the accent is the only colour. That restraint is what makes it look designed.

## Making it yours
1. Replace `colors` with your palette. Keep the roles: one background, one card, one text colour, one accent.
2. Pick a headline font with a heavy weight (700–900) and a mono or narrow font for labels. Put the Google Fonts URL in `fonts.googleFontsUrl`, or add font files to each starter's fonts folder.
3. Put your logo at `brand/logo.svg` (square, works on dark).
4. Render one example from each starter and look at them side by side before you make anything new.

## When to break from your look
- **Reference remakes:** match the reference's palette, motion and sound, and swap only the accent.
- **News carousels:** wear the launching company's look; your logo sits in the corner.

## Safe zones (9:16, 1080x1920)
- Nothing important above **y 240** (the app's top bar) or below **y 1680** (caption and buttons). Captions sit between y 260 and y 1520.
- Covers: key content inside the 3:4 grid crop, **y 240–1680**.

## Real assets only
- Logos from the brand's press kit, Simple Icons or LobeHub icons. Never redraw a logo.
- Product UI from real screenshots (headless Chrome at 2x) or simplified cards built to look like the real screen.
- Never use a real person's likeness except your own, unless you have written permission.
