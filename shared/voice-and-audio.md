# Voice and audio

## Voice options
| Option | Good for | Notes |
|---|---|---|
| Your own read | Talking heads, faceless explainers | The most trusted. Record in a quiet room, phone close. |
| Your cloned voice (ElevenLabs instant clone) | Voiceovers when you can't record | Needs a few minutes of clean audio. Put the voice ID in `brand.json`. |
| A stock narrator | Animated explainers | Pick one and keep it for the whole series. |
| A character voice | Mascot series | One voice per character, always. |
| Local TTS (`npx hyperframes tts`, macOS `say`) | Drafts and testing | Free; fine for timing, weaker for posting. |

- ElevenLabs reads at about 185 words a minute. For a calmer 160, set speed to about 0.87.
- Keep API keys in `.env` (`ELEVENLABS_API_KEY`). Never commit them.

## Word timestamps
`python3 tools/transcribe.py <audio-or-video> words.json` (faster-whisper). Every format keys its visuals to these times. Don't time anything by hand.

## Loudness
Normalise every final render to -14 LUFS: `tools/loudnorm.sh in.mp4 out.mp4`.

See `sound-design.md` for effects and music.
