import sys
import os
import subprocess

# --- Auto-Bootstrap Virtual Environment ---
# Automatically switch to the isolated venv if the user runs 'python main.py' globally
venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Scripts', 'python.exe')
if os.path.exists(venv_python) and sys.executable.lower() != venv_python.lower():
    print("[*] Automatically switching to the isolated virtual environment...")
    sys.exit(subprocess.call([venv_python] + sys.argv))
# ------------------------------------------
import asyncio
import json
import random
import time
import base64
import warnings
import socket
from datetime import datetime
from contextlib import asynccontextmanager

# Suppress ALL deprecation warnings before importing third-party packages
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*urllib3.*chardet.*charset_normalizer.*")
warnings.filterwarnings("ignore", message=".*TripleDES.*")

# Ensure project root is in path for shield_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.websockets import WebSocketState
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from behavioral_trainer import train_user_models
from behavioral_trainer import train_user_models
from honeypot import HoneypotSession, DEMO_COMMANDS, DAVE_MESSAGE, KILL_CHAIN_PHASES, PDFReportHandler, shield_ai
from ml_ensemble import ensemble as ml_ensemble_instance
from live_ml_bridge import run_ensemble_analysis, build_command_telemetry
from scanner import scan_code
from ssh_server import start_ssh_honeypot
from generate_decoy import generate_trackable_pdf, generate_trackable_html
from lateral_interceptor import router as lateral_router, set_broadcast_callback
from ml_engine import ml_router
from middleware import GlobalMonitoringMiddleware
from honeytoken_manager import HoneytokenManager
import database
from sentinel import router as sentinel_router
from impersonator_detector import ImpersonatorDetector


import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
# We will initialize the model only if the key is available
gemini_model = genai.GenerativeModel('gemini-1.5-flash') if GOOGLE_API_KEY else None

# ── Global state ─────────────────────────────────────
sessions: dict[str, HoneypotSession] = {}
monitors: List[WebSocket] = []
file_tracking: Dict[str, Dict[str, Any]] = {}
main_loop = None

@asynccontextmanager
async def lifespan(app):
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
    start_raw_tcp_honeypot(port=8888, broadcast_callback=thread_safe_broadcast)
    
    from lateral_interceptor import token_manager
    # Generate honeytoken decoy files on startup using the shared instance
    token_manager.create_decoy_files()
    
    yield  # Application runs
    # Shutdown logic (if any) goes here

app = FastAPI(title="Labyrinth Forge — DevSecOps Shield v2.0", version="2.0.0", lifespan=lifespan)

app.add_middleware(GlobalMonitoringMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Lateral Movement Interceptor Router
app.include_router(lateral_router)
# Include ML Engine Router
app.include_router(ml_router)

# Include Sentinel Sandbox Router
app.include_router(sentinel_router)

# --- THE IMPERSONATOR ROUTES ---

class BehavioralEvent(BaseModel):
    session_id: str
    user_id: str
    event_type: str
    timestamp: float
    payload: dict

# In-memory store for detectors to avoid reloading models constantly
impersonator_detectors = {}

def get_or_create_detector(session_id, user_id):
    key = f"{session_id}_{user_id}"
    if key not in impersonator_detectors:
        impersonator_detectors[key] = ImpersonatorDetector(session_id, user_id)
    return impersonator_detectors[key]

async def fire_impersonator_alert(event, score_result, severity):
    gemini_narrative = ""
    if gemini_model and severity == 'CRITICAL':
        prompt = f"SECURITY SYSTEM ALERT - Behavioral Anomaly Detected\nSession: {event.session_id}\nUser Profile: {event.user_id}\nImpersonation Risk Score: {score_result['irs']}/100\nSignal breakdown: Isolation Forest: {score_result['if_score']}/100, Sequence Model: {score_result['lstm_score']}/100, File Pattern: {score_result['file_score']}/100\nIn 2-3 sentences, explain what this means and the likely threat. Be direct."
        try:
            response = await asyncio.to_thread(gemini_model.generate_content, prompt)
            gemini_narrative = response.text.strip()
        except Exception as e:
            gemini_narrative = f"Failed to generate narrative: {e}"

    await broadcast_to_monitors({
        'type': 'IMPERSONATOR_ALERT',
        'alert_category': 'BEHAVIORAL_ANOMALY',
        'severity': severity,
        'timestamp': time.time() * 1000,
        'session_id': event.session_id,
        'user_id': event.user_id,
        'irs': score_result['irs'],
        'if_score': score_result['if_score'],
        'lstm_score': score_result['lstm_score'],
        'file_score': score_result['file_score'],
        'gemini_analysis': gemini_narrative,
        'details': f'Behavioral anomaly detected. IRS: {score_result["irs"]}/100.'
    })

@app.post('/api/impersonator/event')
async def submit_behavioral_event(event: BehavioralEvent):
    detector = get_or_create_detector(event.session_id, event.user_id)
    feature_vector = detector.extract_features(event.event_type, event.payload)
    
    if detector.is_learning_phase():
        raw_cmd = event.payload.get('raw_command', '')
        if not raw_cmd:
            raw_cmd = event.payload.get('files_accessed', [''])[0]
        detector.collect_sample(feature_vector, raw_command=raw_cmd)
        if detector.sample_count == 30:
            # Auto-train when learning phase just completed
            await asyncio.to_thread(train_user_models, event.user_id)
            detector.load_models()
            
        return {'phase': 'LEARNING', 'progress': f'{detector.sample_count}/30', 'irs': None}
        
    if not detector.scorer:
        return {'phase': 'ERROR', 'error': 'Model not trained', 'irs': None}

    result = detector.scorer.score_action(feature_vector)
    
    # Inject the command back into the response so the frontend can display it in the timeline
    result['command'] = event.payload.get('raw_command', event.payload.get('files_accessed', [''])[0])
    
    if result['irs'] >= 85:
        await fire_impersonator_alert(event, result, 'CRITICAL')
    elif result['irs'] >= 70:
        await fire_impersonator_alert(event, result, 'WARNING')
        
    return result

@app.get('/api/impersonator/status/{session_id}/{user_id}')
async def get_impersonator_status(session_id: str, user_id: str):
    detector = get_or_create_detector(session_id, user_id)
    if detector.is_learning_phase():
        return {'phase': 'LEARNING', 'progress': f'{detector.sample_count}/30'}
    return {'phase': 'MONITORING', 'progress': '30/30'}

@app.get('/api/impersonator/profile/{session_id}/{user_id}')
async def get_impersonator_profile(session_id: str, user_id: str):
    import os, json
    model_dir = f'model/profiles/{user_id}'
    profile_path = f'{model_dir}/profile.json'
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            return json.load(f)
    return {'error': 'Profile not found'}

@app.post('/api/impersonator/reset/{session_id}/{user_id}')
async def reset_impersonator(session_id: str, user_id: str):
    import os, shutil
    key = f"{session_id}_{user_id}"
    
    # 1. Clear memory
    if key in impersonator_detectors:
        del impersonator_detectors[key]
        
    # 2. Delete json samples
    if os.path.exists('behavioral_samples.json'):
        # Filter out this user's samples
        import json
        with open('behavioral_samples.json', 'r') as f:
            samples = json.load(f)
        samples = [s for s in samples if s['user_id'] != user_id]
        with open('behavioral_samples.json', 'w') as f:
            json.dump(samples, f)
            
    # 3. Delete models
    model_dir = f'model/profiles/{user_id}'
    if os.path.exists(model_dir):
        shutil.rmtree(model_dir)
        
    return {'status': 'reset', 'phase': 'LEARNING', 'progress': '0/30'}

@app.post('/api/impersonator/train/{session_id}/{user_id}')
async def force_train_impersonator(session_id: str, user_id: str):
    try:
        await asyncio.to_thread(train_user_models, user_id)
        detector = get_or_create_detector(session_id, user_id)
        detector.load_models()
        return {'status': 'trained', 'phase': 'MONITORING', 'progress': '30/30'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.get('/api/impersonator/report/{user_id}')
async def get_impersonator_report_data(user_id: str):
    import os, json
    samples_path = 'behavioral_samples.json'
    samples = []
    if os.path.exists(samples_path):
        with open(samples_path, 'r') as f:
            all_samples = json.load(f)
            samples = [s for s in all_samples if s.get('user_id') == user_id]

    baseline_samples = samples[:30]
    result_data = []
    
    for s in baseline_samples:
        cmd = s.get('raw_command', '')
        if not cmd:
            cmd = s.get('raw_files', '')
            
        # The frontend expects avg_dwell, but keystrokes aren't saved in behavioral_samples.json
        # We can approximate it from the feature vector (index 0 is usually avg_dwell)
        # Or just extract it safely if it exists.
        feature_vector = s.get('feature_vector', [])
        avg_dwell = feature_vector[0] if len(feature_vector) > 0 else 0.0
            

        result_data.append({
            'command': cmd,
            'avg_dwell': avg_dwell
        })
        
    return {'status': 'success', 'data': result_data}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


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

def get_lan_ip():
    """Retrieve the actual LAN IP address of this machine instead of 127.0.0.1 for realism."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Does not have to be reachable, just forces the OS to pick an outbound interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.get("/api/runtime/network")
async def get_runtime_network():
    lan_ip = get_lan_ip()
    return {
        "lan_ip": lan_ip,
        "dashboard_url": f"http://{lan_ip}:5173",
        "attacker_console_url": f"http://{lan_ip}:5173/?screen=attacker",
        "ssh_command": f"ssh root@{lan_ip} -p 2222",
        "raw_port_command": f"nc {lan_ip} 8888"
    }

# ── Simple TCP Honeypot (for raw port pinging) ───────
def start_raw_tcp_honeypot(port=8888, broadcast_callback=None):
    def run_raw_server():
        import socket
        import threading
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", port))
            sock.listen(5)
            print(f"[*] Raw TCP Honeypot listening on port {port}")
            while True:
                client, addr = sock.accept()
                threading.Thread(target=handle_raw_client, args=(client, addr, broadcast_callback), daemon=True).start()
        except Exception as e:
            print(f"[!] Raw TCP Honeypot Error: {e}")

    def handle_raw_client(client, addr, broadcast_callback):
        client.send(b"Labyrinth Security System - Authorized Access Only\n\n# ")
        session = HoneypotSession()
        session.session_id = f"raw-{int(time.time())}"
        
        # Notify dashboard of connection
        if broadcast_callback:
            broadcast_callback({
                "type": "init",
                "session_id": session.session_id,
                "attacker_ip": addr[0],
                "message": f"🔌 PORT SCAN DETECTED \u2014 Raw connection from {addr[0]} on port {port}"
            })

        try:
            while True:
                data = client.recv(1024)
                if not data: break
                cmd = data.decode('utf-8', errors='ignore').strip()
                if not cmd: continue
                if cmd.lower() in ["exit", "quit"]: break
                
                output = session.process_command(cmd, addr[0])
                client.send(f"{output}\n\n# ".encode())

                # Enriched ML Telemetry
                if broadcast_callback:
                    # Run async analysis in the thread
                    try:
                        import asyncio
                        from live_ml_bridge import run_ensemble_analysis, build_command_telemetry
                        loop = asyncio.new_event_loop()
                        ensemble_result, ai_narration = loop.run_until_complete(run_ensemble_analysis(session))
                        profile = session.get_profile()
                        attack_intel = session.get_attack_intel()
                        prediction = session.predict_next_move()
                        command_analysis = build_command_telemetry(session, cmd, output, profile, attack_intel, prediction)
                        
                        broadcast_callback({
                            "type": "command",
                            "session_id": session.session_id,
                            "command": cmd,
                            "output": output,
                            "prompt": "# ",
                            "profile": profile,
                            "attack_intel": attack_intel,
                            "prediction": prediction,
                            "command_analysis": command_analysis,
                            "ensemble_analysis": ensemble_result,
                            "ai_narration": ai_narration,
                            "risk_event": command_analysis["risk_score"] > 15,
                            "timestamp": time.time() * 1000
                        })
                        loop.close()
                    except Exception as ex:
                        print(f"Raw ML Error: {ex}")

            client.close()
        except Exception:
            client.close()

    import threading
    threading.Thread(target=run_raw_server, daemon=True).start()

def _parse_user_agent(ua: str) -> dict:
    """Parse a User-Agent string into OS, browser, and device type."""
    ua_lower = ua.lower()
    
    # Detect OS
    if "windows nt 10" in ua_lower:
        os_name = "Windows 10/11"
    elif "windows nt" in ua_lower:
        os_name = "Windows"
    elif "macintosh" in ua_lower or "mac os" in ua_lower:
        os_name = "macOS"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "iphone" in ua_lower:
        os_name = "iOS (iPhone)"
    elif "ipad" in ua_lower:
        os_name = "iOS (iPad)"
    elif "linux" in ua_lower:
        os_name = "Linux"
    elif "cros" in ua_lower:
        os_name = "ChromeOS"
    else:
        os_name = "Unknown OS"
    
    # Detect Browser
    if "edg/" in ua_lower:
        browser = "Microsoft Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
    elif "chrome" in ua_lower and "safari" in ua_lower:
        browser = "Google Chrome"
    elif "firefox" in ua_lower:
        browser = "Mozilla Firefox"
    elif "safari" in ua_lower:
        browser = "Apple Safari"
    else:
        browser = "Unknown Browser"
    
    # Detect Device Type
    if any(x in ua_lower for x in ["mobile", "android", "iphone"]):
        device_type = "MOBILE"
    elif any(x in ua_lower for x in ["tablet", "ipad"]):
        device_type = "TABLET"
    else:
        device_type = "DESKTOP"
    
    return {"os": os_name, "browser": browser, "device_type": device_type}

def _get_ip_geolocation(ip: str) -> dict:
    """Lookup IP geolocation using a free API. Returns location data."""
    is_local = ip in ("127.0.0.1", "::1", "localhost")
    if is_local:
        return {
            "city": "Localhost",
            "region": "Local Network",
            "country": "Local",
            "isp": "Loopback Adapter",
            "org": "Your Machine",
            "lat": 0, "lon": 0,
            "timezone": "Local"
        }
    try:
        import requests as req
        resp = req.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,lat,lon,timezone,isp,org", timeout=3)
        data = resp.json()
        if data.get("status") == "success":
            return {
                "city": data.get("city", "Unknown"),
                "region": data.get("regionName", "Unknown"),
                "country": data.get("country", "Unknown"),
                "isp": data.get("isp", "Unknown ISP"),
                "org": data.get("org", "Unknown Org"),
                "lat": data.get("lat", 0),
                "lon": data.get("lon", 0),
                "timezone": data.get("timezone", "Unknown")
            }
    except Exception as e:
        print(f"[!] IP Geolocation lookup failed: {e}")
    return {
        "city": "Unknown", "region": "Unknown", "country": "Unknown",
        "isp": "Unknown", "org": "Unknown", "lat": 0, "lon": 0, "timezone": "Unknown"
    }

def get_source_intel(request: Request):
    """Generate detailed real-time source fingerprinting for threat analysis."""
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent", "Unknown")
    
    is_local = ip in ("127.0.0.1", "::1")
    parsed_ua = _parse_user_agent(ua)
    geo = _get_ip_geolocation(ip)
    
    network_type = "INTERNAL_VLAN" if is_local else "EXTERNAL_REMOTE"
    hostname = "ADMIN-WORKSPACE" if is_local else f"NODE-{ip.replace('.', '-')}"
    
    return {
        "ip": ip,
        "ua": ua,
        "hostname": hostname,
        "network": network_type,
        "location": f"{geo['city']}, {geo['region']}, {geo['country']}" if not is_local else "Local Datacenter",
        "os": parsed_ua["os"],
        "browser": parsed_ua["browser"],
        "device_type": parsed_ua["device_type"],
        "isp": geo["isp"],
        "org": geo["org"],
        "lat": geo["lat"],
        "lon": geo["lon"],
        "timezone": geo["timezone"],
        "access_time": datetime.now().isoformat()
    }

def is_authorized_access(request: Request, file_id: str = None) -> bool:
    """Check if the request is coming from an authorized environment."""
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent", "Unknown Device")
    
    # Always authorize localhost for testing
    if ip == "127.0.0.1" or ip == "::1":
        return True
        
    if file_id and file_id in file_tracking:
        tracking = file_tracking[file_id]
        return ip == tracking.get("first_ip") and ua == tracking.get("first_ua")
        
    return False

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

# Initialize callback for Lateral Movement Interceptor
set_broadcast_callback(broadcast_to_monitors)

# ── REST Endpoints ───────────────────────────────────

class ScanRequest(BaseModel):
    code: str
    language: str = "python"

class CommandRequest(BaseModel):
    session_id: str
    command: str # Validated via pydantic if using Field, but I'll add manual check for simplicity

class ModeRequest(BaseModel):
    session_id: str
    mode: str  # "ubuntu" | "windows" | "iot"

@app.get("/api/decoys/honeytokens")
def get_honeytoken_registry():
    """Returns the registered honeytokens (simulation helper)."""
    registry_path = "honeytoken_registry.json"
    if os.path.exists(registry_path):
        with open(registry_path, "r") as f:
            # We also need to get the actual values for the simulation to work
            # In a real system this would be a HUGE security risk, but for this
            # localized defensive simulation, we'll expose the .env values
            # to the simulation portal so the 'attacker' can 'discover' them.
            registry = json.load(f)
            
            # Enrich registry with actual values from decoys/.env if available
            env_path = os.path.join("decoys", "honeytokens", ".env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f_env:
                    for line in f_env:
                        if "=" in line:
                            key, val = line.split("=", 1)
                            # Find matching hash
                            for h, info in registry.items():
                                if info["type"] == key.strip():
                                    info["raw_value"] = val.strip()
            return registry
    return {}

@app.get("/")
def root():
    return {"status": "online", "service": "Labyrinth Forge API"}

@app.get("/api/logs")
def get_attack_logs():
    """Returns persistent attack logs from SQLite."""
    return {"logs": database.get_all_logs()}

@app.post("/api/session")
def create_session():
    sid = f"sess-{random.randint(10000,99999)}"
    sessions[sid] = HoneypotSession()
    sessions[sid].session_id = sid
    sessions[sid].broadcast_callback = broadcast_to_monitors
    ip = f"{random.randint(60,220)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
    return {"session_id": sid, "attacker_ip": ip, "prompt": sessions[sid].prompt}

@app.post("/api/command")
def run_command(req: CommandRequest, request: Request):
    session = sessions.get(req.session_id)
    if not session:
        return {"error": "Session not found"}
    ip = get_client_ip(request)
    output = session.process_command(req.command, ip)
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
    from scanner import scan_code
    return scan_code(req.code, req.language)

class ExplainRequest(BaseModel):
    vuln_type: str
    code_context: str

@app.post("/api/scan/explain")
def explain_endpoint(req: ExplainRequest):
    from scanner import shield_ai
    explanation = shield_ai.explain_vulnerability(req.vuln_type, req.code_context)
    return {"explanation": explanation}

class ExecuteRequest(BaseModel):
    code: str
    language: str

@app.post("/api/execute")
def execute_code(req: ExecuteRequest):
    language = req.language.lower()
    
    import tempfile
    import subprocess
    import sys
    import time
    with tempfile.TemporaryDirectory() as temp_dir:
        ext = "py" if language == "python" else "js" if language == "javascript" else "c" if language == "c" else "cpp" if language in ["cpp", "c++"] else "txt"
        file_path = os.path.join(temp_dir, f"source.{ext}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(req.code)
            
        try:
            if language == "python":
                cmd = [sys.executable, file_path]
            elif language == "javascript":
                cmd = ["node", file_path]
            elif language == "c":
                exe_path = os.path.join(temp_dir, "program.exe")
                c_res = subprocess.run(["gcc", file_path, "-o", exe_path], capture_output=True, text=True)
                if c_res.returncode != 0:
                    return {"output": "GCC Compilation Error:\n" + c_res.stderr, "status": "error", "execution_time": "0.000s"}
                cmd = [exe_path]
            elif language in ["cpp", "c++"]:
                exe_path = os.path.join(temp_dir, "program.exe")
                c_res = subprocess.run(["g++", file_path, "-o", exe_path], capture_output=True, text=True)
                if c_res.returncode != 0:
                    return {"output": "G++ Compilation Error:\n" + c_res.stderr, "status": "error", "execution_time": "0.000s"}
                cmd = [exe_path]
            elif language == "java":
                return {"output": "Mock Java execution successful. Sandbox complete.", "status": "success", "execution_time": "0.012s"}
            else:
                return {"error": "Unsupported language", "status": "failed"}

            start_time = time.time()
            # Provide dummy input to prevent gets()/scanf() or input() from hanging the execution sandbox
            dummy_input = "LabyrinthCyberSec_Payload_Test\n" * 10
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                input=dummy_input
            )
            exec_time = time.time() - start_time
            
            output = result.stdout
            if result.stderr:
                output += "\nError Output:\n" + result.stderr
                
            return {
                "output": output,
                "status": "success" if result.returncode == 0 else "error",
                "execution_time": f"{exec_time:.3f}s"
            }
        except subprocess.TimeoutExpired:
            return {"output": "Execution timed out (5s limit exceeded). Possible infinite loop.", "status": "error", "execution_time": "5.000s"}
        except Exception as e:
            return {"output": f"Runtime error: {str(e)}", "status": "error", "execution_time": "0.000s"}

class ExploitRequest(BaseModel):
    vulnerability_id: str
    vulnerability_type: str
    code_snippet: str
    line: int

@app.post("/api/exploit")
async def simulate_exploit(req: ExploitRequest):
    if gemini_model:
        prompt = f"""
        Given the following vulnerability:
        Type: {req.vulnerability_type}
        Line: {req.line}
        Code: {req.code_snippet}
        
        1. Generate a Python HACKING SCRIPT (e.g. using pwntools or requests) that an attacker would use to exploit this vulnerability.
        2. Generate the SIMULATED TERMINAL OUTPUT showing the script executing and successfully compromising the sandbox (e.g. crashing it or leaking data).
        
        Format your response EXACTLY like this:
        [EXPLOIT SCRIPT]
        <script code here>

        [SIMULATION OUTPUT]
        <terminal output here>
        """
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        return {"simulation": response.text.strip()}
    return {"simulation": "[EXPLOIT SCRIPT]\npython -c 'print(\"A\"*200)' | ./vuln\n\n[SIMULATION OUTPUT]\nSegmentation Fault (core dumped)."}

class LiveAttackRequest(BaseModel):
    vulnerable_code: str
    exploit_script: str

@app.post("/api/live_attack")
async def live_attack(req: LiveAttackRequest):
    if gemini_model:
        prompt = f"""
        You are an advanced exploit simulator engine.
        
        Target Vulnerable Code:
        {req.vulnerable_code}
        
        Attacker's Payload/Script:
        {req.exploit_script}
        
        Generate the dramatic, highly-detailed terminal output showing the payload successfully executing and exploiting the vulnerable application. 
        Show realistic exploitation steps (e.g., overflowing buffer, spawning shell, whoami, leaking shadow file, extracting data, etc.).
        Do not explain anything. Output ONLY the raw terminal text output, about 10-15 lines.
        """
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        return {"output": response.text.strip()}
    return {"output": "[!] Offline Mode.\n> Injecting payload...\n> Overwriting instruction pointer...\n> Shell spawned.\nroot@labyrinth:~# "}


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
    is_authorized = is_authorized_access(request, document_name)
    timestamp = datetime.now().isoformat()
    source = get_source_intel(request)
    
    gemini_analysis = "Authorized access from secure endpoint. No threat detected." if is_authorized else "Simulation mode analysis: Highly suspicious internal threat detected."
    
    if gemini_model and not is_authorized:
        try:
            prompt = (
                f"An internal user from IP {source['ip']} using device {source['ua']} "
                f"just accessed a highly restricted decoy file named {document_name} at {timestamp}. "
                "Analyze this security breach, explain why accessing a decoy file indicates "
                "malicious internal intent, and provide a threat severity score from 1-100. "
                "Keep the response under 3 sentences."
            )
            response = await asyncio.to_thread(gemini_model.generate_content, prompt)
            if response and response.text:
                gemini_analysis = response.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")

    alert_data = {
        "type": "INTERNAL_THREAT_ALERT",
        "document_name": document_name,
        "ip_address": source["ip"],
        "user_agent": source["ua"],
        "source_info": source,
        "timestamp": timestamp,
        "gemini_analysis": gemini_analysis,
        "is_authorized": is_authorized
    }
    
    await broadcast_to_monitors(alert_data)
    return {"status": "tracked" if not is_authorized else "authorized", "analysis": gemini_analysis}

@app.get("/api/download/{filename}")
async def download_decoy(filename: str, request: Request):
    """
    Serves a decoy file and triggers a high-priority internal threat alert.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "decoys", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_id = filename.split('.')[0]
    is_authorized = is_authorized_access(request, file_id)
    timestamp = datetime.now().isoformat()
    source = get_source_intel(request)
    
    gemini_analysis = "File download by authorized owner. Secure transfer." if is_authorized else "Simulation mode analysis: High-priority data exfiltration detected via direct download."
    
    if gemini_model and not is_authorized:
        try:
            prompt = (
                f"CRITICAL: An internal user from IP {source['ip']} is DOWNLOADING a decoy file: {filename}. "
                f"This is a deliberate exfiltration attempt detected at {timestamp}. "
                "Analyze the risk of this physical theft/download, identify the intent as malicious data hoarding, "
                "and explain why this is a high-severity breach. Keep it under 3 sentences."
            )
            response = await asyncio.to_thread(gemini_model.generate_content, prompt)
            if response and response.text:
                gemini_analysis = response.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")

    alert_data = {
        "type": "INTERNAL_THREAT_ALERT",
        "document_name": filename,
        "ip_address": source["ip"],
        "user_agent": f"[DOWNLOAD] {source['ua']}",
        "source_info": source,
        "timestamp": timestamp,
        "gemini_analysis": gemini_analysis,
        "is_authorized": is_authorized
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
    try:
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
        if client_ip in ("127.0.0.1", "::1", "localhost"):
            client_ip = get_lan_ip() # Use realistic LAN IP instead of loopback
            
        client_ua = request.headers.get("user-agent", "Unknown Device")
        file_tracking[file_id] = {
            "first_ip": client_ip,
            "first_ua": client_ua,
            "access_history": []
        }
        print(f"[*] Pre-authorized {client_ip} for {file_id}")
            
        return {"message": "Decoy generated", "download_url": f"/api/download/{filename}"}
    except Exception as e:
        print(f"[!] Generate Decoy Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500

@app.get("/api/v1/ghost-pixel/{file_id}")
async def ghost_pixel(file_id: str, request: Request):
    """
    Invisible 1x1 tracking pixel that detects unauthorized file exfiltration (USB, Cloud, etc.)
    """
    source = get_source_intel(request)
    timestamp = datetime.now().isoformat()

    print(f"[*] TRACKING HIT: {source['ip']} | Device: {source['ua']}")
    
    # 1x1 transparent PNG pixel (base64)
    pixel_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")
    
    # --- Smart Authorization Logic ---
    if file_id not in file_tracking:
        # If the file wasn't generated via the API (e.g. pre-deployed)
        # the first person to trigger it becomes the "Authorized Owner"
        print(f"[!] Unknown File Access: Promoting {source['ip']} as Authorized Origin for {file_id}")
        file_tracking[file_id] = {
            "first_ip": source['ip'],
            "first_ua": source['ua'],
            "access_history": []
        }
        
    # Deduplication: Prevent double alerts if HTML fires multiple pixels at once
    history = file_tracking.get(file_id, {}).get("access_history", [])
    if history:
        last_access = history[-1]
        if last_access["ip"] == source["ip"]:
            last_time = datetime.fromisoformat(last_access["timestamp"])
            if (datetime.now() - last_time).total_seconds() < 5:
                print(f"[*] Duplicate ping from {source['ip']} ignored.")
                return Response(content=pixel_data, media_type="image/png")
    
    # Eval against the owner
    is_authorized = is_authorized_access(request, file_id)
    is_movement = not is_authorized
    # --------------------------------
    
    history_entry = {
        "ip": source['ip'],
        "timestamp": timestamp,
        "user_agent": source['ua'],
        "status": "UNAUTHORIZED" if is_movement else "AUTHORIZED"
    }
    file_tracking[file_id]["access_history"].append(history_entry)
    
    if is_movement:
        threat_type = "GEOGRAPHIC ANOMALY" # Simply put, any change from first access
        gemini_analysis = f"[Simulation] Potential data leak detected. File accessed from unauthorized environment."
        
        if gemini_model:
            try:
                prompt = (
                    f"SECURITY ALERT: The honeytoken file '{file_id}' was accessed. "
                    f"Authorized Environment: IP {file_tracking[file_id]['first_ip']}, Device {file_tracking[file_id]['first_ua']}. "
                    f"Current Access: IP {source['ip']}, Device {source['ua']}. "
                    "Analyze the threat. Is this a USB share, a colleague's laptop, or external exfiltration? "
                    "Provide a sharp threat assessment in under 3 sentences."
                )
                response = await asyncio.to_thread(gemini_model.generate_content, prompt)
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
            "current_ip": source['ip'],
            "history": file_tracking[file_id]["access_history"],
            "gemini_analysis": gemini_analysis,
            "timestamp": timestamp,
            "is_authorized": False
        }
        await broadcast_to_monitors(movement_event)
        
        await broadcast_to_monitors({
            "type": "INTERNAL_THREAT_ALERT",
            "document_name": file_id,
            "ip_address": source['ip'],
            "user_agent": f"[UNAUTHORIZED ACCESS] {source['ua']}",
            "source_info": source,
            "gemini_analysis": gemini_analysis,
            "timestamp": timestamp,
            "is_authorized": False
        })
    else:
        # Authorized Hit
        print(f"[*] Authorized heartbeat from {source['ip']}")
        
        # WE SEND A MOVEMENT EVENT EVEN FOR THE FIRST HIT to initialize the map
        await broadcast_to_monitors({
            "type": "FILE_MOVEMENT_DETECTED",
            "file_id": file_id,
            "origin_ip": source['ip'],
            "current_ip": source['ip'],
            "history": file_tracking[file_id]["access_history"],
            "gemini_analysis": "Authorized Origin established.",
            "timestamp": timestamp,
            "is_authorized": True
        })

        await broadcast_to_monitors({
            "type": "INTERNAL_THREAT_ALERT",
            "document_name": file_id,
            "ip_address": source['ip'],
            "user_agent": f"[AUTHORIZED OWNER] {source['ua']}",
            "source_info": source,
            "gemini_analysis": "File accessed from original authorized environment. No threat detected.",
            "timestamp": timestamp,
            "is_authorized": True
        })
    return Response(content=pixel_data, media_type="image/png")

# ── WebSocket — Attacker CLI Bridge ──────────────────────
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
        "message": f"ALERT: LIVE INTRUSION — Attacker connected from {ip} (Local CLI)"
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
                # Run blocking honeypot logic in a thread
                output = await asyncio.to_thread(session.process_command, cmd, ip)
                profile = await asyncio.to_thread(session.get_profile)
                attack_intel = await asyncio.to_thread(session.get_attack_intel)
                prediction = await asyncio.to_thread(session.predict_next_move)
                command_analysis = await asyncio.to_thread(
                    build_command_telemetry, session, cmd, output, profile, attack_intel, prediction
                )
                risk_event = command_analysis["risk_score"] > 15

                # Neural Ensemble ML Analysis
                ensemble_result, ai_narration = await run_ensemble_analysis(session)

                # 1. Send response back to Attacker CLI
                await websocket.send_json({
                    "type": "output",
                    "session_id": sid,
                    "command": cmd,
                    "output": output,
                    "prompt": session.prompt,
                    "profile": profile,
                })

                # 2. Mirror to all Monitor UIs with full ML data
                await broadcast_to_monitors({
                    "type": "command",
                    "session_id": sid,
                    "command": cmd,
                    "output": output,
                    "prompt": session.prompt,
                    "profile": profile,
                    "attack_intel": attack_intel,
                    "prediction": prediction,
                    "command_analysis": command_analysis,
                    "risk_event": risk_event,
                    "ensemble_analysis": ensemble_result,
                    "ai_narration": ai_narration,
                    "timestamp": time.time() * 1000,
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

                output = await asyncio.to_thread(session.process_command, cmd)
                profile = await asyncio.to_thread(session.get_profile)
                attack_intel = await asyncio.to_thread(session.get_attack_intel)
                prediction = await asyncio.to_thread(session.predict_next_move)
                command_analysis = await asyncio.to_thread(
                    build_command_telemetry, session, cmd, output, profile, attack_intel, prediction
                )
                ensemble_result, ai_narration = await _run_ensemble_analysis(session)
                await websocket.send_json({
                    "type": "command",
                    "command": cmd,
                    "output": output,
                    "prompt": session.prompt,
                    "profile": profile,
                    "attack_intel": attack_intel,
                    "prediction": prediction,
                    "command_analysis": command_analysis,
                    "ensemble_analysis": ensemble_result,
                    "ai_narration": ai_narration,
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
        # Session cleanup
        pass

# ── Manual Fingerprint Persistence ────────────────
class FingerprintSaveRequest(BaseModel):
    fingerprint: Dict[str, Any]
    attacker_ip: str

@app.post("/api/v1/fingerprint/save")
async def save_fingerprint(request: FingerprintSaveRequest):
    try:
        from ml_profiler import MLProfiler
        profiler = MLProfiler()
        # We use generate_new_profile to save the data
        # Mapping the incoming fingerprint data back to what generate_new_profile expects
        data = {
            "raw_sequence": request.fingerprint.get("raw_sequence", ""),
            "avg_delay": request.fingerprint.get("avg_time_delay_ms", 0.0) / 1000.0,
            "error_rate": request.fingerprint.get("error_rate_percentage", 0.0)
        }
        res = profiler.generate_new_profile(data, request.attacker_ip)
        if res:
            return {"status": "success", "profile": res}
        return {"status": "error", "message": "Failed to save profile"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Use reload=True for development so changes in honeypot.py etc. take effect immediately
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
