# 🛡️ Labyrinth Forge — DevSecOps Shield v3.0

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Labyrinth Forge** is an advanced, AI-first DevSecOps platform designed to autonomously detect, analyze, and remediate security vulnerabilities. Combining deep-code AST scanning with Large Language Models (LLMs), it provides a complete ecosystem for both proactive defense and reactive threat simulation.

---

## 🚀 Key Features

### 🔍 Vulnerability Scanner & AI Auditor
- **Deep AST Analysis**: Structural code scanning to identify patterns of common vulnerabilities.
- **AI-Powered Explanations**: Uses LLMs (GPT-4 / Gemini) to provide context-aware security insights.
- **Scoring System**: Dynamic security risk assessment and scoring (0-100).

### 🤖 Autonomous AI Remediator
- **Self-Healing Code**: Automatically generates secure patches for detected vulnerabilities.
- **Safety Validation**: Multi-layer structural validation ensures AI-generated fixes don't break existing logic.
- **Hardening Engine**: Proactively wraps vulnerable code in security-hardened patterns.

### 🕸️ War Room (Threat Simulation)
- **Live SSH Honeypots**: Real-time intrusion monitoring on port `2222`.
- **Decoy Management**: Deployment of honey-tokens, fake credentials, and decoy databases.
- **Attacker Profiling**: AI-driven analysis of attacker commands and psychological behavior.

### 📊 Security Intel & Reporting
- **PDF Incident Reports**: Automated generation of forensic reports including kill-chain analysis.
- **Real-time Dashboard**: Live telemetry via WebSockets with a cyber-themed aesthetic.

---

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite, Tailwind CSS, Lucide Icons, Recharts, Xterm.js.
- **Backend**: FastAPI, Python 3.10+, WebSockets (Uvicorn).
- **AI/LLM**: OpenAI API (GPT-4), Google Gemini Pro.
- **Reporting**: ReportLab for professional-grade PDF generation.
- **Protocol Emulation**: Paramiko-based SSH Honeypot.

---

## 📂 Project Structure

```text
├── frontend/             # React application (Vite-powered UI)
├── backend/              # FastAPI server, Honeypot logic & API endpoints
├── devsecops_shield/     # Main orchestration logic for AI auditing
├── shield_engine/        # Core AI engines (LLM, Remediation, Scanner)
├── docs/                 # (Optional) Detailed documentation
└── tests/                # Unit and integration tests
```

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ & npm

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables (create a `.env` file):
   ```env
   OPENAI_API_KEY=your_key_here
   GEMINI_API_KEY=your_key_here
   ```
4. Start the server:
   ```bash
   python main.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

---

## 🛡️ Usage

- **Vulnerability Detector**: Upload or paste code into the DevSecOps tab to run the AI security audit.
- **War Room**: Point your SSH client to `localhost:2222` to simulate an intrusion and monitor it in real-time.
- **Reports**: After a simulation or scan, download the auto-generated PDF for a detailed breakdown of findings.

---

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.

*Developed by the Labyrinth Forge Team.*
