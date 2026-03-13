import os
import asyncio
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.websockets import WebSocketState
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from honeypot import HoneypotSession, DEMO_COMMANDS, DAVE_MESSAGE, KILL_CHAIN_PHASES, PDFReportHandler
from scanner import scan_code
from ssh_server import start_ssh_honeypot
from generate_decoy import generate_trackable_pdf, generate_trackable_html

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
# We will initialize the model only if the key is available
gemini_model = genai.GenerativeModel('gemini-1.5-flash') if GOOGLE_API_KEY else None

app = FastAPI(title="Labyrinth Forge — DevSecOps Shield v2.0", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global state ─────────────────────────────────────
sessions: dict[str, HoneypotSession] = {}
monitors: List[WebSocket] = []
file_tracking: Dict[str, Dict[str, Any]] = {}
main_loop = None

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    # Start SSH Honeypot in background
    print("[*] Initializing SSH Honeypot...")
    
    def thread_safe_broadcast(message):
        if main_loop:
            # Create task instead of run_coroutine_threadsafe to avoid some threading edge cases in uvicorn
            main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(broadcast_to_monitors(message))
            )
        else:
            print("[!] Broadcast failed: main_loop not initialized")
        
    start_ssh_honeypot(port=2222, broadcast_callback=thread_safe_broadcast)

# ... (rest of the code remains the same)

# Add require_token decorator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def require_token(token: HTTPAuthorizationCredentials = Depends(security)):
    if token.token != "your_secret_token":
        raise HTTPException(status_code=401, detail="Invalid token")

# Add secure_b64_decode function
def secure_b64_decode(data: str) -> str:
    try:
        return base64.b64decode(data).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid base64 input")

# Add prefix check
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def get_file_path(filename: str) -> str:
    return os.path.abspath(os.path.join(BASE_DIR, filename))

# ... (rest of the code remains the same)