# 🛡️ Labyrinth Forge: Active Defense Deception Engine

Labyrinth Forge is a next-generation **Active Defense & Cybersecurity Deception Engine**. It transforms your infrastructure from a passive target into a lethal maze for adversaries, using AI-powered honeypots, trackable decoys, and shadow credentials to detect, profile, and neutralize threats in real-time.

---

## 🚀 Core Defense Modules

### 1. 🌐 External Threat Defense (War Room)
*   **AI Honeypots**: Dynamic, high-interaction terminal sessions powered by Google Gemini. The system mimics a vulnerable server, lures attackers, and analyzes their commands to predict the next stage of the kill chain.
*   **SSH Decoy**: A dedicated SSH honeypot (Port 2222) that captures brute-force attempts and lateral movement probes.
*   **Live Threat Map**: A real-time WebSocket dashboard visualizing active probes with a high-tech "Oscilloscope" waveform UI.

### 2. 🕵️ Internal Threat Monitor
*   **The Leaker (Data Exfiltration Tracking)**:
    *   Generates **Trackable Decoys** (PDF/HTML) embedded with stealthy "Ghost Pixels".
    *   Provides **Forensic Intel**: Instant geolocation, ISP data, device fingerprinting, and OS detection upon file opening.
    *   **Exfiltration Tree**: Visualizes how a single leaked file branches across different unauthorized IPs.
*   **The Lateral Mover (Shadow Credentials)**:
    *   **Honeytoken Generator**: Creates realistic fake `.env` and `config.json` files containing "Shadow Credentials" (AWS Keys, MongoDB URIs).
    *   **Lateral Interceptor**: A stealthy API router that mimics internal services. It flags any request using a registered honeytoken.
    *   **Simulation Portal**: An interactive terminal where you can assume roles (Dev, DBA, Auditor) and test the deception system yourself.
*   **The Impersonator (Behavioral Biometrics Engine)**:
    *   **Dual ML Profiling**: Uses scikit-learn `IsolationForest` (for keystroke dynamics and dwell/flight rhythm) and `MLPRegressor` (for sequential command prediction) to profile and verify the operator's identity based solely on typing behavior.
    *   **Real-Time IRS**: Calculates a live Impersonator Risk Score (IRS) from 0-100 to instantly flag anomalous sessions.
    *   **Dynamic Dossier Export**: Includes a high-speed export feature that natively renders a stylized, Cyberpunk-themed PDF training profile of the operator's behavioral baseline.

### 3. 🛡️ DevSecOps Shield (Aegis)
*   **Aegis Scanner**: Automatically scans codebases for vulnerabilities and hardcoded secrets before they reach production.
*   **AI Security Audit**: Uses Gemini to explain complex vulnerabilities and provide remediation steps in natural language.

---

## 🛠️ Technology Stack
*   **Backend**: Python (FastAPI), WebSockets, SQLite.
*   **Frontend**: React (Vite), Tailwind CSS, Lucide Icons, Framer Motion.
*   **AI Engine**: Google Gemini 1.5 Flash (Generative Threat Analysis).
*   **Networking**: Integrated with Ngrok for global callback tracking.

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
# Set your GEMINI_API_KEY in .env
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Initialize Traps
Run the honeytoken generator to create your first set of shadow credentials:
```bash
cd backend
python honeytoken_manager.py
```

---

## 📊 Dashboard Overview
*   **War Room**: Live external attack monitoring.
*   **Internal Threat**: Manage trackable decoys and monitor lateral movement.
*   **Lateral Mover Portal**: Interactive simulation environment for testing "insider threat" scenarios.

---

## ⚖️ License
This project is for educational and authorized defensive purposes only. **Labyrinth Forge** is designed to secure environments, not to harm.

---
**Built by Suman S** | *Active Defense for the Modern Era*
