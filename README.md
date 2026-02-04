# The Donna - Real-time Voice Assistant

A real-time voice chat application featuring Donna Paulson, the Executive Assistant personality. Built with FastAPI, SvelteKit, WebSocket, and Together.ai (Whisper + Kimi 2.5 + Orpheus).

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
              │   Whisper    │          │  Kimi 2.5   │          │   Orpheus    │
              │   (STT)      │          │   (Donna)   │          │   (TTS)      │
              └─────────────┘          └─────────────┘          └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Together.ai API key

### Backend (Railway/Local)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export TOGETHER_API_KEY=your_key_here

# Run locally
uvicorn main:app --reload
```

### Frontend (Local Development)

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Edit .env and set VITE_BACKEND_URL=ws://localhost:8000

# Run development server
npm run dev
```

## Deployment

### Railway (Backend)

1. Connect your GitHub repo to Railway
2. Set environment variables:
   - `TOGETHER_API_KEY`: Your Together.ai API key
3. Deploy

### Vercel/Netlify (Frontend)

1. Connect your repo
2. Set build command: `npm run build`
3. Set output directory: `build`
4. Add environment variable:
   - `VITE_BACKEND_URL`: Your Railway backend WebSocket URL (wss://...)

## Environment Variables

### Backend
| Variable | Description |
|----------|-------------|
| `TOGETHER_API_KEY` | Together.ai API key |
| `PORT` | Server port (default: 8000) |

### Frontend
| Variable | Description |
|----------|-------------|
| `VITE_BACKEND_URL` | WebSocket URL of backend |

## Features

- 🎤 Real-time voice recording with silence detection
- 🗣️ WebSocket-based audio streaming
- 🤖 Together.ai Whisper for speech-to-text
- 💬 Kimi 2.5 with Donna Paulson personality
- 🔊 Together.ai Orpheus for text-to-speech
- 📱 PWA support (install on mobile)
- 🔄 Auto-reconnection

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `WS /ws` - WebSocket for voice chat

## WebSocket Protocol

### Client → Server
```json
{"type": "audio_chunk", "data": "base64_audio"}
{"type": "end_utterance"}
{"type": "ping"}
```

### Server → Client
```json
{"type": "chunk_received"}
{"type": "status", "message": "..."}
{"type": "transcript", "text": "..."}
{"type": "response_text", "text": "..."}
{"type": "audio_response", "audio": "base64_mp3", "format": "mp3"}
{"type": "error", "message": "..."}
{"type": "pong"}
```

## License

MIT