# Looks

A look is everything visual that is not the script: fonts, background, colours, how cards enter, how the slam word is drawn and how scenes cut. The script, the timings and the card types stay the same, so one script can be rendered in any look.

```
python3 gen.py               # the look named in script.json ("dark" in the sample)
python3 gen.py --look paper  # override it for one run
```

Looks live in `make_look()` in `gen.py`. `preview.jpg` shows the sample in both: dark on the top row, paper on the bottom.

## Dark (default)

Built entirely from `brand/brand.json`, so it changes when your brand kit does.

| Part | Value |
| --- | --- |
| Grounds | Two, alternating per scene: `bg` with a soft `accent` glow and a drifting pixel field, then a light ground (`ink` as the background, white cards, `accentStrong` as the accent) |
| Fonts | `fonts.head` for the headline, `fonts.body` for cards, `fonts.mono` for small labels |
| Slam word | Huge, in the accent colour, blurring in |
| Cards | Rise out of a blur |
| Cuts | Pixel dissolve from the previous scene's ground |
| Accent surfaces | Flat accent fill with black or white text, whichever reads better |

## Paper

Taken from a reference reel with a warm, tactile feel. It keeps your brand name, handle and logo but replaces the palette and fonts.

| Part | Value |
| --- | --- |
| Ground | Cream paper `#ede8df` with a faint 54 px grid, slow diagonal window light and a warm vignette, in one composition under every scene |
| Colours | Ink `#141416`, cards `#fbfaf7`, clay accent `#c2552d`, success `#4f8a5b`, danger `#b83a2e` |
| Fonts | EB Garamond for the headline and quotes (serif captions), Inter for cards, JetBrains Mono for labels (all bundled with HyperFrames) |
| Slam word | Serif, with a clay highlight box wiped in behind it and the type turning white |
| Cards | Fly in from the camera and land with a small overshoot, each with a soft thock |
| Cuts | The stage drifts slowly, then blurs up and away |
| Accent surfaces | "Clay": a vertical gradient, a hard bottom edge and an inner highlight, so buttons, bars and ticks look moulded |

## Matching a reference's look

1. Grab five or six frames of the reference (`ffmpeg -ss <t> -i ref.mp4 -frames:v 1 f.png`) and put them side by side with `preview.jpg`.
2. Write down, as numbers: the background colour and texture, the type family and weight for captions, the accent colour, the card radius and shadow, how things enter (blur, slide, land, pop) and how scenes change.
3. Copy the `paper` block in `make_look()`, rename it and change those values. The keys:
   - `grounds`: one or more colour sets; scenes cycle through them.
   - `head`, `body`, `mono`: font families. A family HyperFrames bundles works by name; any other needs a file such as `brand/fonts/MyFont.woff2` (the file name, minus spaces, must match the family).
   - `entrance`: `rise` or `land`. `slam`: `big` or `box`. `transition`: `dissolve` or `drift`. `backdrop`: `pixels` or `paper`. `clay`: true for moulded accent surfaces.
4. Re-run `gen.py --look <name>`, snapshot and compare with the reference frames again. Match the look and the motion, not just the colours.
