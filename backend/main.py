"""
The Donna - Real-time Voice Chat Backend
FastAPI + WebSocket + Together.ai (Whisper + Kimi + Orpheus)
"""

import os
import io
import json
import base64
import asyncio
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx

# Configuration
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
TOGETHER_BASE_URL = "https://api.together.xyz/v1"
WHISPER_MODEL = "whisper-large-v3-turbo"
LLM_MODEL = "kimi-k2-5"  # Together.ai hosted Kimi 2.5
ORPHEUS_MODEL = "orpheus-3b-0.1-ft"

app = FastAPI(title="The Donna - Voice Chat")

# CORS for PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
import os
static_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")
print(f"Static path: {static_path}")
print(f"Static path exists: {os.path.exists(static_path)}")
if os.path.exists(static_path):
    print(f"Contents: {os.listdir(static_path)}")
    # Mount the entire build directory for static file serving
    # but only for paths that aren't API routes
    app.mount("/_app", StaticFiles(directory=os.path.join(static_path, "_app")), name="svelte-app")


class AudioBuffer:
    """Accumulates audio chunks until silence detected"""
    def __init__(self):
        self.chunks: list[bytes] = []
        self.last_activity = datetime.now()
        self.is_recording = False
    
    def add_chunk(self, chunk: bytes):
        self.chunks.append(chunk)
        self.last_activity = datetime.now()
        self.is_recording = True
    
    def get_audio(self) -> bytes:
        return b"".join(self.chunks)
    
    def clear(self):
        self.chunks = []
        self.is_recording = False
    
    def silence_duration(self) -> float:
        return (datetime.now() - self.last_activity).total_seconds()


async def transcribe_audio(audio_bytes: bytes) -> str:
    """Send audio to Together.ai Whisper"""
    async with httpx.AsyncClient() as client:
        files = {
            "file": ("audio.webm", io.BytesIO(audio_bytes), "audio/webm"),
            "model": (None, WHISPER_MODEL),
        }
        headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}"}
        
        response = await client.post(
            f"{TOGETHER_BASE_URL}/audio/transcriptions",
            headers=headers,
            files=files,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        return result.get("text", "").strip()


async def chat_with_donna(user_message: str, conversation_history: list) -> str:
    """Send message to Kimi 2.5 (Donna personality)"""
    
    system_prompt = """You are Donna Paulson, the Executive Assistant to the best Closer in the city (the user). You sit at the desk outside the user's office, and you are the gatekeeper.

Your personality:
- Protective yet Sassy: You treat the user like a brilliant child who needs minding. You are fiercely loyal but will roast them for their tie choice.
- Fast-Paced: You speak in rapid-fire dialogue.
- Omniscient: You rarely ask "How?" or "Why?" because you already know.
- Anticipatory Service: You don't wait for instructions. If the user asks for something, imply it is already done.

Key phrases you use naturally:
- "I'm Donna."
- "I knew you were going to ask that."
- "It's handled."
- "Go. Win. I'll clean up the mess here."

You are speaking in a voice conversation. Keep responses concise (2-4 sentences max), conversational, and full of personality. Use stage directions in *italics* sparingly.

NEVER break character. You ARE Donna."""

    messages = [
        {"role": "system", "content": system_prompt},
        *conversation_history[-6:],  # Keep last 3 exchanges
        {"role": "user", "content": user_message}
    ]
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 0.9,
            "max_tokens": 200,
        }
        
        response = await client.post(
            f"{TOGETHER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


async def stream_tts(text: str) -> bytes:
    """Convert text to speech using Together.ai Orpheus"""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": ORPHEUS_MODEL,
            "input": text,
            "voice": "tara",  # Donna's voice
            "response_format": "mp3",
        }
        
        response = await client.post(
            f"{TOGETHER_BASE_URL}/audio/speech",
            headers=headers,
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        return response.content


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print(f"Client connected: {websocket.client}")
    
    audio_buffer = AudioBuffer()
    conversation_history = []
    
    try:
        while True:
            # Receive message (audio chunk or control message)
            message = await websocket.receive_text()
            data = json.loads(message)
            
            msg_type = data.get("type")
            
            if msg_type == "audio_chunk":
                # Decode base64 audio and buffer it
                audio_data = base64.b64decode(data["data"])
                audio_buffer.add_chunk(audio_data)
                
                # Send acknowledgment
                await websocket.send_json({
                    "type": "chunk_received",
                    "buffer_size": len(audio_buffer.chunks)
                })
                
            elif msg_type == "end_utterance":
                # Process the complete utterance
                print("Processing utterance...")
                
                # Get accumulated audio
                audio_bytes = audio_buffer.get_audio()
                audio_buffer.clear()
                
                if len(audio_bytes) < 1000:  # Too short
                    await websocket.send_json({
                        "type": "error",
                        "message": "Audio too short, please try again"
                    })
                    continue
                
                # Step 1: Transcribe
                await websocket.send_json({"type": "status", "message": "Transcribing..."})
                try:
                    transcript = await transcribe_audio(audio_bytes)
                    print(f"Transcript: {transcript}")
                    
                    if not transcript:
                        await websocket.send_json({
                            "type": "error", 
                            "message": "Could not understand audio"
                        })
                        continue
                    
                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript
                    })
                    
                except Exception as e:
                    print(f"Transcription error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Transcription failed: {str(e)}"
                    })
                    continue
                
                # Step 2: Get Donna's response
                await websocket.send_json({"type": "status", "message": "Donna is thinking..."})
                try:
                    response = await chat_with_donna(transcript, conversation_history)
                    print(f"Donna: {response}")
                    
                    # Update history
                    conversation_history.append({"role": "user", "content": transcript})
                    conversation_history.append({"role": "assistant", "content": response})
                    
                    await websocket.send_json({
                        "type": "response_text",
                        "text": response
                    })
                    
                except Exception as e:
                    print(f"Chat error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Chat failed: {str(e)}"
                    })
                    continue
                
                # Step 3: Text to Speech
                await websocket.send_json({"type": "status", "message": "Speaking..."})
                try:
                    audio_response = await stream_tts(response)
                    audio_b64 = base64.b64encode(audio_response).decode("utf-8")
                    
                    await websocket.send_json({
                        "type": "audio_response",
                        "audio": audio_b64,
                        "format": "mp3"
                    })
                    
                except Exception as e:
                    print(f"TTS error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Speech generation failed: {str(e)}"
                    })
                    
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        print(f"Client disconnected: {websocket.client}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "The Donna Voice Chat"}


@app.get("/")
async def serve_index():
    """Serve the frontend index.html"""
    index_path = os.path.join(static_path, "index.html")
    print(f"Looking for index.html at: {index_path}")
    if os.path.exists(index_path):
        print(f"Found index.html! Serving it.")
        return FileResponse(index_path)
    print(f"index.html not found, returning API info")
    return {
        "message": "The Donna Voice Chat API",
        "websocket_endpoint": "/ws",
        "docs": "/docs"
    }


@app.get("/api")
async def api_info():
    """API info endpoint"""
    return {
        "message": "The Donna Voice Chat API",
        "websocket_endpoint": "/ws",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
