---
name: short-form-formats
description: Make proven short-form video and carousel formats (talking head, faceless explainer, reference remake, cinematic explainer, avatar creator, game parody, mascot series, animated explainer, AI video with overlays, news carousel) in your own brand. Use when asked for a reel, TikTok, Short or carousel, when given a reference to remake, for a cover or caption, or to pick a format for a topic. Holds per-format steps, runnable Remotion, HyperFrames and carousel starters, and shared rules for script, voice, sound, motion, covers and posting.
---

# Short-form formats

Ten formats that were each delivered and tested on real accounts. Each has a guide in `formats/`, pictures in `examples/`, and most have a runnable starter in `starters/`.

**First, read `brand/brand.json`.** It holds the user's colours, fonts, logo, voice, CTA and banned phrases. If it still says "Your Brand", ask the user to fill it in (see `ADAPT.md`) before making anything they'll post.

## 1. Pick the format

| The user wants… | Format | Guide | Starter |
|---|---|---|---|
| Themselves on camera, news or a review, fast cuts | Talking head | `formats/talking-head.md` | `starters/remotion-kit` |
| A voice-led explainer, no face, kinetic words and UI cards | Faceless explainer | `formats/faceless-explainer.md` | `starters/hyperframes-explainer` |
| "Make one like this" (a reference link) | Reference remake | `formats/reference-remake.md` | `starters/hyperframes-explainer` |
| A short concept film plus a vertical cut | Cinematic explainer | `formats/cinematic-explainer.md` | HyperFrames style sampling |
| A UGC-style creator video without filming | Avatar creator | `formats/avatar-creator.md` | HyperFrames + avatar video |
| Product vs a chore, as a joke | Game parody | `formats/game-parody.md` | `starters/remotion-kit` |
| Episodes with a brand character | Mascot series | `formats/mascot-series.md` | `starters/remotion-kit` |
| An animated feature, number, news or checklist reel | Animated explainer | `formats/animated-explainer.md` | `starters/remotion-kit` |
| Cinematic AI shots with designed overlays | AI video with overlays | `formats/ai-video-overlay.md` | `starters/remotion-kit` |
| A photo carousel: a launch or a how-to | News carousel | `formats/news-carousel.md` | `starters/carousel` |

If two fit, ask one short question. News about a tool → talking head. A reference link → run `shared/reference-intake.md` first.

## 2. Shared steps (every format)
1. **Angle:** start from what the user is excited about (`shared/script-and-captions.md`).
2. **Script:** hook in three layers, 30–75 s, a verdict. Check every product claim against the product's own site or docs.
3. **Voice:** the user's read, their clone or a narrator (`shared/voice-and-audio.md`). Get word timestamps with `tools/transcribe.py`.
4. **Build:** copy the starter, then key every visual to a spoken word (`shared/motion-language.md`).
5. **Sound:** a cue on every motion event (`shared/sound-design.md`), then `tools/loudnorm.sh`.
6. **Review:** `tools/contact_sheet.py`; fix anything outside the safe zone (`shared/brand-and-look.md`).
7. **Cover:** `shared/covers.md`.
8. **Deliver:** caption, a phone copy (`tools/phone_copy.sh`) and `shared/posting-checklist.md`.

## 3. Rules
- Real logos and real product UI, never redrawn ones.
- No banned phrases from `brand.json`.
- Never a real person's likeness except the user's own, unless they have written permission.
- AI-content label on for avatars, AI characters and AI video.
- "Comment WORD" CTAs only when DM automation is live.
- Keys live in `.env`. Never print or commit them.
- Never post, schedule or send without the user's yes.
