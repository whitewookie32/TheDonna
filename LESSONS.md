# The Donna - Lessons Learned

A post-mortem on building a real-time voice AI assistant.

## What Worked

### 1. WebSocket Architecture
- Real-time bidirectional communication worked well
- Binary audio streaming via base64 encoding was reliable
- Auto-reconnection logic kept sessions alive

### 2. Together.ai Integration
- **Whisper (STT)**: Once we got the model name right (`openai/whisper-large-v3`), transcription was excellent
- **DeepSeek-V3 (LLM)**: Fast, cheap, high-quality responses
- **Pricing**: Together.ai is genuinely affordable for experimentation

### 3. Character Design
- The "Donna Paulson" persona was fun and engaging
- System prompt engineering worked well for personality consistency
- Stage directions (*sighs*, *adjusts glasses*) added flavor

### 4. Tech Stack Choices
- FastAPI + SvelteKit is a solid combo
- Railway deployment was painless
- PWA approach for mobile was the right call

## What Didn't Work

### 1. Audio Format Conversion
**The Problem:**
- Browser MediaRecorder outputs WebM (Opus codec)
- Together.ai Whisper expects WAV or MP3
- Required ffmpeg in Docker container
- Added 2-5 seconds of latency per conversion

**What We Tried:**
- Direct WebM upload → Failed (format not recognized)
- ffmpeg conversion → Worked but slow and complex
- pydub (Python audio lib) → Required ffmpeg anyway

**Lesson:** Real-time voice is hard because **browsers and AI APIs speak different audio languages**.

### 2. Model Naming Chaos
**The Problem:**
Together.ai's model names are inconsistently formatted:

| What We Tried | What Actually Worked |
|---------------|---------------------|
| `kimi-k2-5` | `deepseek-ai/DeepSeek-V3` |
| `orpheus-3b-0.1-ft` | `canopylabs/orpheus-3b-0.1-ft` |
| `openai/whisper-large-v3-turbo` | `openai/whisper-large-v3` |
| `cartesia/sonic-3` | Never fully tested |

**Lesson:** Provider APIs change. What works today may 404 tomorrow. Abstract model selection behind a config file.

### 3. TTS Playback Issues
**The Problem:**
- Generated audio but browser wouldn't autoplay
- Chrome requires user interaction before audio can play
- Format confusion (MP3 vs WAV vs WebM)
- Audio elements need proper MIME types

**What We Tried:**
- MP3 format → Browser compatibility issues
- WAV format → Large file sizes
- Base64 data URIs → Worked but clunky

**Lesson:** Browser audio autoplay restrictions make "voice assistants in the browser" a UX nightmare. Native apps handle this better.

### 4. The Simplicity Realization
**The Problem:**
We built a complex system for voice chat when the user already had:
- A working Telegram bot (this one!)
- Voice note capability in Telegram
- No latency issues
- No deployment complexity

**The Pivot:**
Instead of fixing TheDonna, the user realized they could just... send voice notes to their AI assistant directly. Same result, zero infrastructure.

**Lesson:** Sometimes the best solution is the one you already have.

## Technical Debt Accumulated

1. **No audio format abstraction** - Hardcoded WebM→WAV conversion
2. **No model fallback** - If Together.ai changed a model name, everything broke
3. **No graceful degradation** - Failed TTS should have fallen back to text-only
4. **No retry logic** - API 404s should have been caught and retried with different models

## What We'd Do Differently

### 1. Use a Managed Voice API
Instead of stitching together STT → LLM → TTS, use a unified service:
- **Option A**: OpenAI's Realtime API (WebSocket, handles everything)
- **Option B**: Vapi.ai (purpose-built voice AI infrastructure)
- **Option C**: Bland.ai (voice AI with personas)

### 2. Build Native First
Browser-based voice assistants fight an uphill battle against:
- Autoplay restrictions
- Audio codec limitations
- Background tab throttling

A native mobile app (React Native, Flutter) would handle audio better.

### 3. Separate Concerns
The monolithic approach (one backend doing everything) made debugging hard:
- STT issues looked like TTS issues
- WebSocket errors masked API errors
- No way to test components in isolation

Better architecture:
```
Audio Service (handles browser audio) → Queue → STT Service → Queue → LLM Service → Queue → TTS Service → Queue → Audio Service
```

### 4. Start with Text, Add Voice Later
We built voice-first. Big mistake. Should have:
1. Built text chat with Donna personality (works immediately)
2. Added voice input as enhancement
3. Added voice output as final polish

Voice is a multiplier on complexity, not an add-on.

## The Real Lesson

**"The best code is no code."**

The user had a simpler solution available the whole time:
- Voice notes in Telegram
- No deployment
- No model management
- No audio format conversion
- Works on every device they own

Sometimes building is the wrong move. Sometimes you just need to use what's already there.

## Resources for Future Voice AI Builders

If you're reading this and want to build something similar:

### Managed Voice APIs
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime) - WebSocket-based, handles everything
- [Vapi.ai](https://vapi.ai) - Voice AI infrastructure
- [Bland.ai](https://bland.ai) - Conversational voice AI
- [Retell.ai](https://retell.ai) - Voice AI for phone calls

### Self-Hosted Options
- [Whisper](https://github.com/openai/whisper) - Run STT locally
- [Ollama](https://ollama.ai) - Local LLMs
- [Piper](https://github.com/rhasspy/piper) - Fast local TTS
- [Coqui TTS](https://github.com/coqui-ai/TTS) - Neural TTS

### Browser Audio Libraries
- [RecordRTC](https://github.com/muaz-khan/RecordRTC) - Better MediaRecorder wrapper
- [wavesurfer.js](https://wavesurfer-js.org/) - Audio visualization
- [howler.js](https://howlerjs.com/) - Cross-browser audio playback

## Final Thoughts

TheDonna was fun to build. We learned about:
- WebSocket binary streaming
- Audio format conversion
- Together.ai's quirks
- Browser audio limitations
- When to quit

The project failed not because of technical incompetence, but because **we were solving the wrong problem**. The user didn't need a voice assistant - they needed to talk to their AI. And they already could.

**Know when to hold 'em, know when to fold 'em.**

---

*Archived 2026-02-05*
