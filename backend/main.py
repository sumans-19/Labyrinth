import sys
import os
import asyncio
import json
import random
import time
import base64
from datetime import datetime

# Ensure project root is in path for shield_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
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

def get_client_ip(request: Request):
    """Robust client IP detection for proxies like Ngrok."""
    # Check for Ngrok specific forwarding
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # The true client IP is the first one in the list
        ip = forwarded.split(",")[0].strip()
        # Clean up IPv6 formatting if needed
        if ip.startswith("::ffff:"):
            ip = ip[7:]
        return ip
        
    # Standard client host
    host = request.client.host if request.client else "Unknown"
    if host == "127.0.0.1" or host == "::1":
        # Check if we are behind a proxy that uses X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
    return host

async def broadcast_to_monitors(message: dict):
    """Send a message to all connected monitor UIs."""
    if not monitors:
        # print("DEBUG: No monitors connected.")
        return
        
    print(f"[*] Broadcasting {message.get('type')} to {len(monitors)} monitor(s)")
    disconnected = []
    for ws in monitors:
        try:
            # Check if socket is still open before sending
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.send_json(message)
            else:
                disconnected.append(ws)
        except Exception as e:
            print(f"[!] Broadcast failed for client: {e}")
            disconnected.append(ws)
            
    for ws in disconnected:
        if ws in monitors:
            monitors.remove(ws)
            print(f"[*] Removed dead monitor, {len(monitors)} remaining")

# ── REST Endpoints ───────────────────────────────────

class ScanRequest(BaseModel):
    code: str

class CommandRequest(BaseModel):
    session_id: str
    command: str # Validated via pydantic if using Field, but I'll add manual check for simplicity

class ModeRequest(BaseModel):
    session_id: str
    mode: str  # "ubuntu" | "windows" | "iot"

@app.get("/")
def root():
    return {"status": "online", "service": "Labyrinth Forge API"}

@app.post("/api/session")
def create_session():
    sid = f"sess-{random.randint(10000,99999)}"
    sessions[sid] = HoneypotSession()
    ip = f"{random.randint(60,220)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
    return {"session_id": sid, "attacker_ip": ip, "prompt": sessions[sid].prompt}

@app.post("/api/command")
def run_command(req: CommandRequest):
    session = sessions.get(req.session_id)
    if not session:
        return {"error": "Session not found"}
    output = session.process_command(req.command)
    return {
        "output": output,
        "prompt": session.prompt,
        "profile": session.get_profile(),
    }

@app.post("/api/hydra")
def switch_mode(req: ModeRequest):
    session = sessions.get(req.session_id)
    if not session:
        return {"error": "Session not found"}
    session.mode = req.mode
    session.cwd = "/" if req.mode != "windows" else "C:\\"
    return {"mode": req.mode, "prompt": session.prompt}

@app.post("/api/scan")
def scan_endpoint(req: ScanRequest):
    return scan_code(req.code)

class ExplainRequest(BaseModel):
    vuln_type: str
    code_context: str

@app.post("/api/scan/explain")
def explain_endpoint(req: ExplainRequest):
    from scanner import shield_ai
    explanation = shield_ai.explain_vulnerability(req.vuln_type, req.code_context)
    return {"explanation": explanation}

@app.get("/api/report/download/{session_id}")
def download_pdf_report(session_id: str):
    """Session-based PDF download (requires active session)."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in memory")
    
    report = session.generate_report()
    pdf_handler = PDFReportHandler()
    pdf_bytes = pdf_handler.generate(report)
    filename = f"Labyrinth_Incident_{report['report_id']}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@app.post("/api/report/generate")
def generate_pdf_from_data(report: Dict[str, Any]):
    """Stateless PDF generation (receives data from frontend)."""
    try:
        pdf_handler = PDFReportHandler()
        pdf_bytes = pdf_handler.generate(report)
        filename = f"Labyrinth_Incident_{report.get('report_id', 'Unknown')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Generation Failed: {str(e)}")

@app.get("/api/report/{session_id}")
def get_report(session_id: str):
    session = sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}
    return session.generate_report()

@app.get("/api/decoys")
def get_decoys():
    return {
        "files": [
            {"name": "Q3_Financials.pdf", "type": "pdf", "size": "2.4 MB", "status": "deployed", "icon": "file-text"},
            {"name": "passwords.xlsx", "type": "excel", "size": "156 KB", "status": "deployed", "icon": "table"},
            {"name": "network_diagram.png", "type": "image", "size": "890 KB", "status": "deployed", "icon": "image"},
            {"name": "aws_credentials.bak", "type": "config", "size": "512 B", "status": "active-lure", "icon": "key"},
            {"name": "prod.env", "type": "config", "size": "1.1 KB", "status": "active-lure", "icon": "shield"},
            {"name": "db_dump_2024.sql.gz", "type": "database", "size": "234 MB", "status": "deployed", "icon": "database"},
        ]
    }

@app.get("/api/honeytoken/{document_name}")
async def honeytoken_tripwire(document_name: str, request: Request):
    """
    Invisible tripwire route that detects when an internal user accesses a restricted decoy file.
    """
    ip_address = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown Device")
    timestamp = datetime.now().isoformat()
    
    gemini_analysis = "Simulation mode analysis: Highly suspicious internal threat detected."
    
    if gemini_model:
        try:
            prompt = (
                f"An internal user from IP {ip_address} using device {user_agent} "
                f"just accessed a highly restricted decoy file named {document_name} at {timestamp}. "
                "Analyze this security breach, explain why accessing a decoy file indicates "
                "malicious internal intent, and provide a threat severity score from 1-100. "
                "Keep the response under 3 sentences."
            )
            response = gemini_model.generate_content(prompt)
            if response and response.text:
                gemini_analysis = response.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")

    alert_data = {
        "type": "INTERNAL_THREAT_ALERT",
        "document_name": document_name,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "timestamp": timestamp,
        "gemini_analysis": gemini_analysis
    }
    
    await broadcast_to_monitors(alert_data)
    return {"status": "tracked", "analysis": gemini_analysis}

@app.get("/api/download/{filename}")
async def download_decoy(filename: str, request: Request):
    """
    Serves a decoy file and triggers a high-priority internal threat alert.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "decoys", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    ip_address = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown Device")
    timestamp = datetime.now().isoformat()
    
    gemini_analysis = "Simulation mode analysis: High-priority data exfiltration detected via direct download."
    
    if gemini_model:
        try:
            prompt = (
                f"CRITICAL: An internal user from IP {ip_address} is DOWNLOADING a decoy file: {filename}. "
                f"This is a deliberate exfiltration attempt detected at {timestamp}. "
                "Analyze the risk of this physical theft/download, identify the intent as malicious data hoarding, "
                "and explain why this is a high-severity breach. Keep it under 3 sentences."
            )
            response = gemini_model.generate_content(prompt)
            if response and response.text:
                gemini_analysis = response.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")

    alert_data = {
        "type": "INTERNAL_THREAT_ALERT",
        "document_name": filename,
        "ip_address": ip_address,
        "user_agent": f"[DOWNLOAD] {user_agent}",
        "timestamp": timestamp,
        "gemini_analysis": gemini_analysis
    }
    
    await broadcast_to_monitors(alert_data)
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.post("/api/v1/generate-decoy")
async def api_generate_decoy(request: Request):
    """
    API endpoint to generate and return a trackable document.
    """
    data = await request.json()
    filename = data.get("filename", "decoy.html")
    base_url = data.get("base_url", f"http://{request.client.host}:8000") # Fallback to request host
    
    file_id = filename.split('.')[0]
    temp_path = os.path.join("decoys", filename)
    
    # Ensure decoys dir exists
    os.makedirs("decoys", exist_ok=True)
    
    if filename.endswith('.pdf'):
        generate_trackable_pdf(file_id, temp_path, base_url)
    else:
        # Default to HTML for best compatibility
        generate_trackable_html(file_id, temp_path, base_url)

    # Pre-authorize you (the creator) as the official origin
    client_ip = get_client_ip(request)
    client_ua = request.headers.get("user-agent", "Unknown Device")
    file_tracking[file_id] = {
        "first_ip": client_ip,
        "first_ua": client_ua,
        "access_history": []
    }
    print(f"[*] Pre-authorized {client_ip} for {file_id}")
        
    return {"message": "Decoy generated", "download_url": f"/api/download/{filename}"}

@app.get("/api/v1/ghost-pixel/{file_id}")
async def ghost_pixel(file_id: str, request: Request):
    """
    Invisible 1x1 tracking pixel that detects unauthorized file exfiltration (USB, Cloud, etc.)
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown Device")
    timestamp = datetime.now().isoformat()

    print(f"[*] TRACKING HIT: {ip_address} | Device: {user_agent}")
    
    # 1x1 transparent PNG pixel (base64)
    pixel_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")
    
    # --- Smart Authorization Logic ---
    if file_id not in file_tracking or not file_tracking[file_id].get("access_history"):
        # First time anyone is opening this file!
        # This person is automatically the "Authorized Owner"
        print(f"[!] New File Access: Promoting {ip_address} as Authorized Origin for {file_id}")
        file_tracking[file_id] = {
            "first_ip": ip_address,
            "first_ua": user_agent,
            "access_history": []
        }
    
    # Eval against the owner
    is_ip_change = ip_address != file_tracking[file_id]["first_ip"]
    is_ua_change = user_agent != file_tracking[file_id]["first_ua"]
    is_movement = is_ip_change or is_ua_change
    # --------------------------------
    
    history_entry = {
        "ip": ip_address,
        "timestamp": timestamp,
        "user_agent": user_agent,
        "status": "UNAUTHORIZED" if is_movement else "AUTHORIZED"
    }
    file_tracking[file_id]["access_history"].append(history_entry)
    
    if is_movement:
        threat_type = "GEOGRAPHIC ANOMALY" if is_ip_change else "DEVICE ANOMALY (SHARING DETECTED)"
        gemini_analysis = f"[Simulation] Potential data leak detected. File accessed from {'new network' if is_ip_change else 'unauthorized device on same network'}."
        
        if gemini_model:
            try:
                prompt = (
                    f"SECURITY ALERT: The honeytoken file '{file_id}' was accessed. "
                    f"Authorized Environment: IP {file_tracking[file_id]['first_ip']}, Device {file_tracking[file_id]['first_ua']}. "
                    f"Current Access: IP {ip_address}, Device {user_agent}. "
                    f"Move Type: {'IP Change' if is_ip_change else 'Device Change on Same Wi-Fi'}. "
                    "Analyze the threat. Is this a USB share, a colleague's laptop, or external exfiltration? "
                    "Provide a sharp threat assessment in under 3 sentences."
                )
                response = gemini_model.generate_content(prompt)
                if response and response.text:
                    gemini_analysis = response.text.strip()
            except Exception as e:
                print(f"Gemini Tracking Analysis Error: {e}")

    if is_movement:
        # SAME MOVEMENT EVENT LOGIC ...
        movement_event = {
            "type": "FILE_MOVEMENT_DETECTED",
            "file_id": file_id,
            "origin_ip": file_tracking[file_id]["first_ip"],
            "current_ip": ip_address,
            "history": file_tracking[file_id]["access_history"],
            "gemini_analysis": gemini_analysis,
            "timestamp": timestamp,
            "is_authorized": False
        }
        await broadcast_to_monitors(movement_event)
        
        await broadcast_to_monitors({
            "type": "INTERNAL_THREAT_ALERT",
            "document_name": file_id,
            "ip_address": ip_address,
            "user_agent": f"[{threat_type}] {user_agent}",
            "gemini_analysis": gemini_analysis,
            "timestamp": timestamp,
            "is_authorized": False
        })
    else:
        # Authorized Hit
        print(f"[*] Authorized heartbeat from {ip_address}")
        
        # WE SEND A MOVEMENT EVENT EVEN FOR THE FIRST HIT to initialize the map
        await broadcast_to_monitors({
            "type": "FILE_MOVEMENT_DETECTED",
            "file_id": file_id,
            "origin_ip": ip_address,
            "current_ip": ip_address,
            "history": file_tracking[file_id]["access_history"],
            "gemini_analysis": "Authorized Origin established.",
            "timestamp": timestamp,
            "is_authorized": True
        })

        await broadcast_to_monitors({
            "type": "INTERNAL_THREAT_ALERT",
            "document_name": file_id,
            "ip_address": ip_address,
            "user_agent": f"[AUTHORIZED ACCESS] {user_agent}",
            "gemini_analysis": "File accessed from original authorized environment. No threat detected.",
            "timestamp": timestamp,
            "is_authorized": True
        })

    return Response(content=pixel_data, media_type="image/png")

# ── WebSocket — Attacker CLI Bridge ──────────────────
@app.websocket("/ws/attacker")
async def attacker_ws(websocket: WebSocket):
    try:
        await websocket.accept()
    except Exception as e:
        print(f"[!] Failed to accept attacker WS: {e}")
        return
    
    sid = f"live-{random.randint(1000,9999)}"
    session = HoneypotSession()
    sessions[sid] = session
    # Use real IP from the WebSocket connection
    client_host = websocket.client.host if websocket.client else "unknown"
    ip = client_host

    # Notify monitors of a new connection
    init_payload = {
        "type": "init",
        "session_id": sid,
        "attacker_ip": ip,
        "prompt": session.prompt,
        "message": f"🔥 LIVE INTRUSION — Attacker connected from {ip} (Local CLI)"
    }
    try:
        await broadcast_to_monitors(init_payload)
        await websocket.send_json(init_payload)
    except Exception as e:
        print(f"[!] Failed to send init payload: {e}")
        return

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "command":
                cmd = msg["command"]
                output = session.process_command(cmd)
                profile = session.get_profile()
                
                # 1. Send response back to Attacker CLI
                await websocket.send_json({
                    "type": "output",
                    "output": output,
                    "prompt": session.prompt
                })

                # 2. Mirror to all Monitor UIs
                await broadcast_to_monitors({
                    "type": "command",
                    "command": cmd,
                    "output": output,
                    "prompt": session.prompt,
                    "profile": profile,
                    "attack_intel": session.get_attack_intel(),
                    "prediction": session.predict_next_move(),
                    "risk_event": session.calculate_command_risk(cmd) > 15
                })
    except (WebSocketDisconnect, RuntimeError, ConnectionResetError):
        pass
    except Exception as e:
        print(f"[!] Attacker WS Error: {e}")
    finally:
        try:
            report_data = session.generate_report(ip)
            report_data["session_id"] = sid
            sessions[sid] = session
            await broadcast_to_monitors({
                "type": "isolated",
                "message": "🔌 ATTACKER DISCONNECTED — Session Terminated",
                "report": report_data
            })
        except Exception:
            pass

@app.websocket("/ws/monitor")
async def monitor_ws(websocket: WebSocket):
    try:
        await websocket.accept()
        print(f"[*] Monitor connected. Total monitors: {len(monitors) + 1}")
        monitors.append(websocket)
        while True:
            data = await websocket.receive()
            if data["type"] == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[!] Monitor WS Error: {e}")
    finally:
        if websocket in monitors:
            monitors.remove(websocket)
            print(f"[*] Monitor disconnected. Remaining: {len(monitors)}")

# ── WebSocket — demo mode auto simulation ────────────
@app.websocket("/ws/demo")
async def demo_ws(websocket: WebSocket):
    await websocket.accept()
    session = HoneypotSession()
    sid = f"demo-{random.randint(10000,99999)}"
    sessions[sid] = session
    ip = f"{random.randint(60,220)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"

    await websocket.send_json({
        "type": "init",
        "session_id": sid,
        "attacker_ip": ip,
        "prompt": session.prompt,
        "message": "⚠️  INTRUSION DETECTED — Attacker connected from " + ip,
    })
    await asyncio.sleep(1.5)

    deception_phases = [
        "🔍 Analyzing typing speed...",
        "🧪 Fingerprinting attacker tools...",
        "🍯 Deploying honey-token...",
        "📂 Generating decoy files...",
        "🔒 Locking decoys with tripwire...",
        "🧠 Profiling psychological pattern...",
        "🕸️ Expanding deception surface...",
    ]

    try:
        for i, (cmd, delay) in enumerate(DEMO_COMMANDS):
            try:
                # Send deception status update
                if i < len(deception_phases):
                    await websocket.send_json({
                        "type": "deception",
                        "message": deception_phases[i],
                        "phase": i + 1,
                        "total_phases": len(deception_phases),
                    })

                # Simulate typing delay
                await asyncio.sleep(delay)

                output = session.process_command(cmd)
                await websocket.send_json({
                    "type": "command",
                    "command": cmd,
                    "output": output,
                    "prompt": session.prompt,
                    "profile": session.get_profile(),
                    "attack_intel": session.get_attack_intel(),
                    "prediction": session.predict_next_move(),
                })

                # Dave from IT appears after 8 commands
                if i == 8 and not session.dave_triggered:
                    session.dave_triggered = True
                    session.frustration = min(100, session.frustration + 20)
                    await asyncio.sleep(1.0)
                    await websocket.send_json({
                        "type": "dave",
                        "message": DAVE_MESSAGE,
                        "profile": session.get_profile(),
                    })
            except WebSocketDisconnect:
                raise  # Re-raise disconnect so outer handler catches it
            except Exception as e:
                print(f"[!] Demo command '{cmd}' failed: {e}, continuing...")
                continue

        # Final isolation
        await asyncio.sleep(2.0)
        session.isolated = True
        report_data = session.generate_report(ip)
        report_data["session_id"] = sid # Ensure frontend has the SID for download
        
        await websocket.send_json({
            "type": "isolated",
            "message": "🛑 HACKER ISOLATED — Threat Neutralized",
            "profile": session.get_profile(),
            "attack_intel": session.get_attack_intel(),
            "report": report_data,
        })
    except WebSocketDisconnect:
        pass
    finally:
        # Do NOT pop sid immediately - keep it for 30 minutes for report download
        # In a real app, use a cleanup task.
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
