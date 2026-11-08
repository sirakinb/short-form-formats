# Sound design

**The rule:** one sound cue on every motion event. Sound is half of why a dense edit feels expensive.

## Packs to synthesise (no licensing needed)
| Pack | Sounds | Use with |
|---|---|---|
| Tech | short digital ticks (rotate 3 variants), a glitch hit | Talking-head cuts, full-screen slams |
| Soft UI | thocks on landings, clicks, airy whooshes, glassy chimes | Paper or cream looks, reference remakes |
| Game | punches, K.O. boom, combo blips | Game parody |
| Security | blips, sonar, lock clicks, alarm, sub drop, scan sweep | Security or "danger" topics |

The starters synthesise these with numpy or ffmpeg; see `starters/hyperframes-explainer/sfx.py`.

## Levels
- Ticks under the voice at about 0.13 volume.
- When matching a reference, split its audio with demucs and measure how far the background sits under the voice (often about 10 dB) and how dense the onsets are.
- Music: none by default. Add a trending sound in the app when posting, or a quiet bed for faceless explainers.

## In HyperFrames
Write the cues into one mixed SFX track from the same script that places the motion, so they can never drift apart.
