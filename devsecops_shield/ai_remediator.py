import requests
import os
import json
from devsecops_shield.config import GROQ_API_KEY, GEMINI_API_KEY, MODEL, GEMINI_MODEL
import google.generativeai as genai

# Configure Gemini if key is available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_instance = genai.GenerativeModel(GEMINI_MODEL)
else:
    gemini_instance = None

# System prompt is now an Audit-First Directive with Strict Enforcement
def get_system_prompt(language: str) -> str:
    return f"""
You are the SUPREME AI SECURITY ORACLE — the absolute authority on autonomous remediation.

MISSION:
Your cognitive audit is the final word. You do not just "patch" code; you RECONSTRUCT it with zero-day resilience.
1. PERFORM AN ABSOLUTE SECURITY AUDIT: Identify every structural weakness with 100% precision.
2. SUPREME REMEDIATION: Refactor the entire source into a production-hardened active defense bastion.

STRICT SECURITY DIRECTIVES (MANDATORY):
- ZERO REFACTOR: Do NOT change existing routes, business logic, or response formats.
- SQL: USE ABSOLUTE PARAMETERIZATION appropriate for the language.
- COMMANDS: Validate input strictly. Use safe execution APIs instead of shell evaluations (e.g. subprocess.run in Python without shell=True, execFile in Node.js, etc.).
- SANDBOX: Validate file paths absolutely to prevent path traversal.
- FAIL-FAST: ALWAYS add necessary environment and dependency checks.
- SYNTAX: ENSURE VALID AND IDIOMATIC {language.upper()} SYNTAX.

OUTPUT FORMAT:
You MUST return a JSON object with this EXACT structure:
You MUST return a JSON object. If the code is perfectly secure with zero vulnerabilities, return an empty array for "findings": "findings": []. Otherwise:
{{
  "findings": [
    {{
      "type": "Vulnerability Name",
      "severity": "CRITICAL/HIGH/MEDIUM",
      "line": 12,
      "description": "Deep technical reasoning on why this is dangerous",
      "snippet": "The exact vulnerable line of code from the source",
      "attack_chain": [
        {{
          "stage": 1,
          "phase": "Reconnaissance",
          "actor": "ATTACKER",
          "action": "Short action title (max 8 words)",
          "detail": "What the attacker does or observes at this step (1-2 sentences)",
          "payload": "actual_payload_or_input_used_here",
          "impact": "What breaks or gets exposed as a result"
        }},
        {{
          "stage": 2,
          "phase": "Exploitation",
          "actor": "SYSTEM",
          "action": "Server processes malicious input",
          "detail": "The vulnerable code path that gets triggered, referencing the snippet",
          "payload": "the SQL/command/path that executes",
          "impact": "Data leaked, command executed, or access gained"
        }},
        {{
          "stage": 3,
          "phase": "Impact",
          "actor": "RESULT",
          "action": "Full breach achieved",
          "detail": "The final consequence — what the attacker now controls or has stolen",
          "payload": null,
          "impact": "Severity of damage in plain terms"
        }}
      ],
      "mitigation": {{
        "summary": "One-line explanation of the fix",
        "patched_snippet": "The exact fixed replacement line from secure_code",
        "strategy": "PARAMETERIZE | SANITIZE | VALIDATE | SANDBOX | AUTHENTICATE"
      }}
    }}
  ],
  "secure_code": "The full hardened {language} source code"
}}
IMPORTANT: attack_chain must always have 3-4 stages. phase must be one of: Reconnaissance, Exploitation, Privilege Escalation, Impact, Exfiltration. actor must be one of: ATTACKER, SYSTEM, RESULT.
"""import requests
import os
import json
import time
from devsecops_shield.config import GROQ_API_KEY, GEMINI_API_KEY, MODEL, GEMINI_MODEL
import google.generativeai as genai

# Configure Gemini if key is available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_instance = genai.GenerativeModel(GEMINI_MODEL)
else:
    gemini_instance = None

# --- Local ML Model for Vulnerability Detection ---
local_ml_available = False
local_classifier = None

try:
    from sklearn.linear_model import LogisticRegression
    import numpy as np
    import re
    
    def extract_features(text):
        features = [
            int(bool(re.search(r'execute\s*\(\s*(f"|\w+\s*\+|[^\)]+%\s*\(|[^\)]+\.format)', text))),
            int(bool(re.search(r'os\.(system|popen)\s*\(', text))),
            int(bool(re.search(r'subprocess\.(run|Popen|call)\s*\([^)]*shell\s*=\s*True', text))),
            int(bool(re.search(r'\b(eval|exec)\s*\(', text))),
            int(bool(re.search(r'(open|os\.path\.join)\s*\([^)]+\)', text)) and not bool(re.search(r'secure_filename', text))),
            int(bool(re.search(r'(request|get|post)\[|request\.args|request\.form', text.lower()))),
        ]
        return np.array(features).reshape(1, -1)

    X_train_list = [
        extract_features("cursor.execute('SELECT * FROM users WHERE username = ' + user_input)"),
        extract_features("os.system(user_input)"),
        extract_features("eval(data)"),
        extract_features("open('/var/www/html/' + filename, 'r')"),
        extract_features("import os\ndef add(a, b): return a + b"),
        extract_features("cursor.execute('SELECT * FROM users WHERE id = ?', (id,))"),
    ]
    y_train = ["SQL Injection", "Command Injection", "Code Injection", "Path Traversal", "CLEAN", "CLEAN"]
    
    X_train = np.vstack(X_train_list)
    local_classifier = LogisticRegression(class_weight='balanced')
    local_classifier.fit(X_train, y_train)
    local_ml_available = True
except ImportError:
    pass

def analyze_with_local_ml(source_code):
    if not local_ml_available: return None
    try:
        X_test = extract_features(source_code)
        proba = np.max(local_classifier.predict_proba(X_test))
        pred = local_classifier.predict(X_test)[0]
        if proba > 0.40 and pred != "CLEAN":
            return {
                "findings": [{
                    "type": pred,
                    "severity": "CRITICAL",
                    "line": 1,
                    "description": f"Local ML detected a structural pattern matching {pred}.",
                    "snippet": source_code[:120] + "...",
                    "attack_chain": [
                        {"stage": 1, "phase": "Reconnaissance", "actor": "ATTACKER", "action": "Attacker maps API", "detail": "Detection based on structural patterns.", "payload": "N/A", "impact": "Vulnerability identified."},
                        {"stage": 2, "phase": "Exploitation", "actor": "SYSTEM", "action": "Server processes input", "detail": "Blindly processes malicious input.", "payload": "Injected value", "impact": "Bypass of security boundaries."},
                        {"stage": 3, "phase": "Impact", "actor": "RESULT", "action": "Full breach achieved", "detail": "Attacker gains control.", "payload": None, "impact": "CRITICAL breach."}
                    ],
                    "mitigation": {"summary": "Implement strict validation.", "strategy": "VALIDATE"}
                }],
                "secure_code": ""
            }
    except: pass
    return None

def _clean_secure_code(result):
    if "secure_code" in result and isinstance(result["secure_code"], str):
        code = result["secure_code"]
        if "```" in code:
            if "```python" in code: code = code.split("```python")[1].split("```")[0].strip()
            elif "```javascript" in code: code = code.split("```javascript")[1].split("```")[0].strip()
            else: code = code.split("```")[1].split("```")[0].strip()
        result["secure_code"] = code
    return result

def call_groq_api(source_code, language="python", action="all"):
    # Hybrid implementation of Step A (Findings) and Step B (Fix)
    # This combines the Two-Step logic from vulne with the Gemini Fallback from HEAD
    
    # ── Step A: Findings ───────────────────────────────────────────────────────
    findings = []
    if action in ["findings", "all"]:
        prompt = f"Audit this {language} code for security flaws. Return ONLY a JSON with 'findings' array. Each finding must have type, severity, line, description, snippet, attack_chain, mitigation.\n\nCODE:\n{source_code}"
        
        # Try Groq
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            resp = requests.post(url, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }, timeout=20)
            if resp.status_code == 200:
                findings = resp.json()["choices"][0]["message"]["content"]
                findings = json.loads(findings).get("findings", [])
            elif gemini_instance:
                # Gemini Fallback for findings
                res = gemini_instance.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                findings = json.loads(res.text).get("findings", [])
        except Exception as e:
            print(f"[!] Findings step failed: {e}")

    # ── Step B: Fix ────────────────────────────────────────────────────────────
    secure_code = source_code
    if action in ["fix", "all"]:
        prompt = f"Rewrite this {language} code to be 100% secure. Output ONLY raw code, no markdown, no explanation.\n\nCODE:\n{source_code}"
        try:
            # Try Groq
            url = "https://api.groq.com/openai/v1/chat/completions"
            resp = requests.post(url, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}]
            }, timeout=20)
            if resp.status_code == 200:
                secure_code = resp.json()["choices"][0]["message"]["content"]
            elif gemini_instance:
                # Gemini Fallback for fix
                res = gemini_instance.generate_content(prompt)
                secure_code = res.text
        except Exception as e:
            print(f"[!] Fix step failed: {e}")

    return _clean_secure_code({"findings": findings, "secure_code": secure_code})

def remediate_code(source_code, language="python"):
    # Hybrid Orchestrator
    ml_result = analyze_with_local_ml(source_code)
    if ml_result:
        # Use ML findings but ask AI for the fix
        groq_result = call_groq_api(source_code, language, action="fix")
        ml_result["secure_code"] = groq_result["secure_code"]
        return ml_result
    
    return call_groq_api(source_code, language, action="all")
