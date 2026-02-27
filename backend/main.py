import sys
import os
import asyncio
import json
import random
import time

# Ensure project root is in path for shield_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from honeypot import HoneypotSession, DEMO_COMMANDS, DAVE_MESSAGE, KILL_CHAIN_PHASES, PDFReportHandler
from scanner import scan_code
from ssh_server import start_ssh_honeypot

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
main_loop = None

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    # Start SSH Honeypot in background
    print("[*] Initializing SSH Honeypot...")
    
    def thread_safe_broadcast(message):
        if main_loop:
            asyncio.run_coroutine_threadsafe(broadcast_to_monitors(message), main_loop)
        
    start_ssh_honeypot(port=2222, broadcast_callback=thread_safe_broadcast)

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
            if ws.client_state.value == 1: # CONNECTED
                await ws.send_json(message)
            else:
                disconnected.append(ws)
        except Exception as e:
            print(f"[!] Broadcast failed for {ws.client}: {e}")
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

# ── WebSocket — Attacker CLI Bridge ──────────────────
@app.websocket("/ws/attacker")
async def attacker_ws(websocket: WebSocket):
    await websocket.accept()
    sid = f"live-{random.randint(1000,9999)}"
    session = HoneypotSession()
    sessions[sid] = session
    ip = "127.0.0.1" # Local CLI connection

    # Notify monitors of a new connection
    init_payload = {
        "type": "init",
        "session_id": sid,
        "attacker_ip": ip,
        "prompt": session.prompt,
        "message": f"🔥 LIVE INTRUSION — Attacker connected from {ip} (Local CLI)"
    }
    await broadcast_to_monitors(init_payload)
    await websocket.send_json(init_payload)

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
    except WebSocketDisconnect:
        report_data = session.generate_report(ip)
        report_data["session_id"] = sid
        sessions[sid] = session # Persist live session for 30m
        await broadcast_to_monitors({
            "type": "isolated",
            "message": "🔌 ATTACKER DISCONNECTED — Session Terminated",
            "report": report_data
        })

@app.websocket("/ws/monitor")
async def monitor_ws(websocket: WebSocket):
    await websocket.accept()
    print(f"[*] Monitor connected from {websocket.client}. Total monitors: {len(monitors) + 1}")
    monitors.append(websocket)
    try:
        while True:
            # Use receive() to handle all message types including close/disconnect
            data = await websocket.receive()
            if data["type"] == "websocket.disconnect":
                break
    except Exception as e:
        print(f"[!] Monitor WS Error ({websocket.client}): {e}")
    finally:
        if websocket in monitors:
            monitors.remove(websocket)
            print(f"[*] Monitor disconnected: {websocket.client}. Remaining: {len(monitors)}")

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
