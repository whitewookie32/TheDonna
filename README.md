# The Donna - Voice Assistant (Archived)

> **⚠️ PROJECT SUNSET**  
> This project has been archived and is no longer maintained.  
> The live deployment has been removed from Railway.  
> The code remains here as a reference snapshot.

---

## What It Was

A real-time voice chat application featuring "Donna Paulson" - an Executive Assistant personality powered by Together.ai (Whisper + LLM + TTS).

Built with:
- **Backend**: FastAPI + WebSocket
- **Frontend**: SvelteKit PWA
- **AI Stack**: Together.ai (Whisper STT, DeepSeek-V3 LLM, Cartesia TTS)
- **Deployment**: Railway

## Architecture

```
┌─────────────────┐      WebSocket       ┌──────────────┐
│  Svelte PWA     │◄────────────────────►│   Railway    │
│  (Browser)      │   (Real-time audio)  │   Backend    │
└─────────────────┘                      └──────┬───────┘
                                                │
                       ┌────────────────────────┼────────────────────────┐
                       │                        │                        │
                       ▼                        ▼                        ▼
              ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
              │   Together   │          │   Together   │          │   Together   │
              │   Whisper    │          │  DeepSeek   │          │   Cartesia   │
              │   (STT)      │          │    V3       │          │   (TTS)      │
              └─────────────┘          └─────────────┘          └─────────────┘
```

## Why It Ended

The project reached a point of diminishing returns:

1. **Audio Format Hell** - Browser WebM → Whisper WAV conversion required ffmpeg, adding complexity
2. **API Model Whack-a-Mole** - Together.ai's model naming conventions kept changing (`kimi-k2-5` → `deepseek-ai/DeepSeek-V3`, `orpheus-3b-0.1-ft` → `cartesia/sonic-3`)
3. **TTS Integration Issues** - Audio playback in browsers is finicky; autoplay restrictions, format support
4. **Simpler Alternative** - The user realized they could just... talk to their AI assistant directly in Telegram

## Key Lessons

See [LESSONS.md](./LESSONS.md) for a detailed post-mortem.

## Code Structure

```
TheDonna/
├── backend/
│   ├── main.py           # FastAPI + WebSocket server
│   ├── requirements.txt  # Python deps
│   └── Dockerfile        # Container config
├── frontend/
│   ├── src/              # SvelteKit source
│   ├── static/           # Static assets
│   └── build/            # Production build
└── README.md             # This file
```

## Running Locally (For Reference)

```bash
# Backend
cd backend
pip install -r requirements.txt
export TOGETHER_API_KEY=your_key
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## License

MIT - Do whatever you want with this code.

---

*"It's handled." - Donna Paulson*
