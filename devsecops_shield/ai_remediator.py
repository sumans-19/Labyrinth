import requests
import os
import json
from devsecops_shield.config import GROQ_API_KEY, MODEL

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
"""

# --- Local ML Model for Vulnerability Detection ---
local_ml_available = False
local_classifier = None

try:
    from sklearn.linear_model import LogisticRegression
    import numpy as np
    import re
    
    def extract_features(text):
        # Extract meaningful structural features from the code to make the ML model highly robust
        # We look for dangerous structural combinations, not just the presence of a function.
        features = [
            # SQL Injection: cursor.execute(...) contains string concatenation/f-string
            int(bool(re.search(r'execute\s*\(\s*(f"|\w+\s*\+|[^\)]+%\s*\(|[^\)]+\.format)', text))),
            
            # Command Injection: os.system or os.popen
            int(bool(re.search(r'os\.(system|popen)\s*\(', text))),
            
            # Command Injection: subprocess with shell=True
            int(bool(re.search(r'subprocess\.(run|Popen|call)\s*\([^)]*shell\s*=\s*True', text))),
            
            # Code Injection: eval or exec
            int(bool(re.search(r'\b(eval|exec)\s*\(', text))),
            
            # Path Traversal: open(...) or os.path.join(...) WITHOUT secure_filename
            int(bool(re.search(r'(open|os\.path\.join)\s*\([^)]+\)', text)) and not bool(re.search(r'secure_filename', text))),
            
            # Context feature: Contains web input
            int(bool(re.search(r'(request|get|post)\[|request\.args|request\.form', text.lower()))),
        ]
        return np.array(features).reshape(1, -1)

    # Train a robust local model using engineered features
    X_train_list = [
        # SQL Injection
        extract_features("cursor.execute('SELECT * FROM users WHERE username = ' + user_input)"),
        extract_features("query = f\"SELECT * FROM data WHERE id = {user_id}\"\ncursor.execute(query)"),
        extract_features("execute('UPDATE users SET pass = %s WHERE user = %s' % (p, u))"),
        # Command Injection
        extract_features("os.system(user_input)"),
        extract_features("subprocess.run('ping -c 4 ' + user_input, shell=True)"),
        extract_features("os.popen(cmd).read()"),
        # Code Injection
        extract_features("eval(data)"),
        extract_features("exec(code)"),
        # Path Traversal
        extract_features("open('/var/www/html/' + filename, 'r')"),
        extract_features("os.path.join(BASE_DIR, fname)"),
        
        # CLEAN - Secured variations
        extract_features("import os\ndef add(a, b): return a + b"),
        extract_features("print('Hello world')"),
        extract_features("x = 5 + 3"),
        extract_features("cursor.execute('SELECT * FROM users WHERE id = ?', (id,))"), # Secure parameterization
        extract_features("subprocess.run(cmd.split(), shell=False)"), # Secure subprocess
        extract_features("os.path.join(BASE_DIR, secure_filename(fname))"), # Secure path traversal
    ]
    
    y_train = [
        "SQL Injection", "SQL Injection", "SQL Injection",
        "Command Injection", "Command Injection", "Command Injection",
        "Code Injection", "Code Injection",
        "Path Traversal", "Path Traversal",
        "CLEAN", "CLEAN", "CLEAN", "CLEAN", "CLEAN", "CLEAN"
    ]
    
    X_train = np.vstack(X_train_list)
    local_classifier = LogisticRegression(class_weight='balanced')
    local_classifier.fit(X_train, y_train)
    local_ml_available = True
    print("[*] Local ML Model (Robust Feature Extractor) initialized successfully.")
except ImportError:
    print("[!] scikit-learn not found. Local ML model disabled. Falling back to Groq AI.")

def analyze_with_local_ml(source_code):
    if not local_ml_available:
        return None
    try:
        X_test = extract_features(source_code)
        proba = np.max(local_classifier.predict_proba(X_test))
        pred = local_classifier.predict(X_test)[0]
        
        # Very robust now, so we can use a standard threshold
        if proba > 0.40 and pred != "CLEAN":
            return {
                "findings": [{
                    "type": pred,
                    "severity": "CRITICAL",
                    "line": 1,
                    "description": f"The source code is vulnerable to {pred}. Unsanitized input is being passed directly into an execution sink. This allows an attacker to manipulate the execution flow, fundamentally breaking the logic of the application and leading to unauthorized data access or complete system compromise.",
                    "snippet": source_code[:120] + "...",
                    "attack_chain": [
                        {
                            "stage": 1,
                            "phase": "Reconnaissance",
                            "actor": "ATTACKER",
                            "action": "Attacker maps API endpoints",
                            "detail": "The attacker identifies an input parameter and tests it with special characters or payloads.",
                            "payload": "?input=test' OR 1=1; ls -la",
                            "impact": "Application behaves unexpectedly, confirming injection vulnerability."
                        },
                        {
                            "stage": 2,
                            "phase": "Exploitation",
                            "actor": "SYSTEM",
                            "action": "Server processes malicious input",
                            "detail": "The application blindly processes the malicious payload and passes it directly to the execution sink.",
                            "payload": "Executed payload",
                            "impact": "The original boundaries are neutralized, causing the system to execute the attacker's commands."
                        },
                        {
                            "stage": 3,
                            "phase": "Impact",
                            "actor": "RESULT",
                            "action": "Full breach achieved",
                            "detail": "The attacker successfully compromises the system, gaining unauthorized access to sensitive data or execution control.",
                            "payload": None,
                            "impact": "CRITICAL. Complete breach of system confidentiality and integrity."
                        }
                    ],
                    "mitigation": {
                        "summary": "Implement strict validation and use parameterized APIs or safe execution wrappers.",
                        "patched_snippet": "# See fully secure code below",
                        "strategy": "PARAMETERIZE | VALIDATE"
                    }
                }],
                "secure_code": "" # To be filled by Groq
            }
        elif pred == "CLEAN":
            # Local ML should ONLY be a fast-lane for known vulnerabilities.
            print("[*] Local ML didn't find known vulnerabilities. Forwarding to Groq for deep audit...")
            return None
            
    except Exception as e:
        print(f"[!] Local ML Error: {e}")
    return None

def _call_groq(messages, response_format=None, max_tokens=4096, temperature=0.1):
    """Low-level Groq HTTP call with retry logic and model fallback."""
    import time
    
    MODELS_TO_TRY = [MODEL, "gemma2-9b-it", "llama-3.1-70b-versatile"]
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    last_error = None
    for model in MODELS_TO_TRY:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Only add response_format if explicitly requested; some model/format combos
        # cause a 400 on older Groq model versions.
        if response_format:
            payload["response_format"] = response_format

        for attempt in range(3):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=90)
                
                if response.status_code == 429:
                    wait = 5 * (attempt + 1)
                    print(f"[!] Groq rate-limited (model={model}, attempt={attempt+1}). Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                if response.status_code == 400:
                    # Bad request — likely json_object format not supported by this model; retry without it
                    print(f"[!] Groq 400 on model={model}: {response.text[:200]}. Retrying without response_format...")
                    payload.pop("response_format", None)
                    continue

                if not response.ok:
                    print(f"[!] Groq HTTP {response.status_code} on model={model}: {response.text[:300]}")
                    response.raise_for_status()

                content = response.json()["choices"][0]["message"]["content"]
                if model != MODEL:
                    print(f"[*] Used fallback model: {model}")
                return content

            except requests.exceptions.Timeout:
                print(f"[!] Groq timeout (model={model}, attempt={attempt+1}/3)")
                last_error = "Timeout"
                time.sleep(5)
            except Exception as e:
                print(f"[!] Groq error (model={model}, attempt={attempt+1}/3): {type(e).__name__}: {e}")
                last_error = str(e)
                if attempt < 2:
                    time.sleep(5)

        print(f"[!] All attempts failed for model={model}, trying next...")

    raise RuntimeError(f"Groq API: all models failed. Last error: {last_error}")



def call_groq_api(source_code, language="python", action="all"):
    """
    Calls Groq in two specialized steps (or one, if `action` specifies it):
    Step A — Get precise JSON findings + attack chain.
    Step B — Get the full, complete, hardened secure code as plain text.
    """
    import time

    findings = []
    secure_code = source_code  # safe fallback = original

    # ── Step A: Vulnerability Analysis (JSON) ──────────────────────────────────
    if action in ["findings", "all"]:
        try:
            findings_system = f"""You are a precise security auditor for {language.upper()} code. Your job is to find REAL, EXPLOITABLE vulnerabilities only.

CRITICAL RULES — READ CAREFULLY:
1. A vulnerability only exists if an attacker can ACTUALLY exploit it right now.
2. DO NOT flag code that is already properly secured. Examples of SAFE patterns:
   - SQL: cursor.execute("SELECT ... WHERE x=?", (val,))  ← SAFE, parameterized
   - SQL: cursor.execute("SELECT ... WHERE x=%s", (val,)) ← SAFE, parameterized  
   - Subprocess: subprocess.run(["cmd", arg], shell=False) ← SAFE, no shell injection
   - File: os.path.abspath() + path validation + restricted base dir ← SAFE
   - Passwords: werkzeug/bcrypt/argon2 hash + check_password_hash() ← SAFE
3. ONLY flag genuine issues such as:
   - SQL: cursor.execute(f"... {{user_input}}") or string concatenation → SQL Injection
   - OS: os.system(user_input) or subprocess(shell=True, cmd=user_input) → Command Injection
   - File: open(user_input) without path validation → Path Traversal
   - Passwords: stored as plain text or compared with == → Insecure Auth
   - eval(user_input) or exec(user_input) → Code Injection
4. If the code is clean and secure, you MUST return {{"findings": []}} — no exceptions.

Return ONLY a JSON object (no markdown, no explanation):
{{
  "findings": [
    {{
      "type": "Vulnerability Name",
      "severity": "CRITICAL",
      "line": 1,
      "description": "Precise technical explanation of why this specific line is exploitable",
      "snippet": "the exact vulnerable line from the code",
      "attack_chain": [
        {{"stage": 1, "phase": "Reconnaissance", "actor": "ATTACKER", "action": "Brief title", "detail": "What attacker does", "payload": "example payload", "impact": "what breaks"}},
        {{"stage": 2, "phase": "Exploitation", "actor": "SYSTEM", "action": "System processes input", "detail": "vulnerable path triggered", "payload": "injected value", "impact": "data leaked or command run"}},
        {{"stage": 3, "phase": "Impact", "actor": "RESULT", "action": "Full breach achieved", "detail": "what attacker now controls", "payload": null, "impact": "severity in plain terms"}}
      ],
      "mitigation": {{"summary": "One-line fix", "patched_snippet": "fixed replacement line", "strategy": "PARAMETERIZE"}}
    }}
  ]
}}
If the code has NO exploitable vulnerabilities, return exactly: {{"findings": []}}"""


            raw = _call_groq(
                messages=[
                    {"role": "system", "content": findings_system},
                    {"role": "user", "content": source_code}
                ],
                response_format={"type": "json_object"},
                max_tokens=2048,
            )
            # Strip accidental markdown wrappers
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            parsed = json.loads(raw)
            findings = parsed.get("findings", [])
        except Exception as e:
            print(f"[!] Groq findings step failed: {e}")

    # ── Step B: Full Secure Code Generation (plain text, no JSON wrapping) ──────
    if action in ["fix", "all"]:
        try:
            code_system = f"""You are an expert secure coding engineer.
Your ONLY job is to rewrite the provided {language.upper()} code to fix ALL security vulnerabilities.
Rules:
- Output ONLY the raw {language.upper()} source code. No markdown, no explanation, no triple backticks, no commentary.
- Keep the SAME routes, functions, and business logic — only fix the security issues.
- The output MUST be the COMPLETE, RUNNABLE source file — never truncate it.
- Fix: SQL injection → parameterized queries. Command injection → subprocess without shell=True. Path traversal → validate/restrict paths. XSS → escape output or use safe templates. Insecure deserialization → use JSON."""

            secure_code = _call_groq(
                messages=[
                    {"role": "system", "content": code_system},
                    {"role": "user", "content": f"Rewrite this code to be fully secure:\n\n{source_code}"}
                ],
                response_format=None,   # plain text, NOT json_object — avoids truncation
                max_tokens=8192,        # allow the full file to be output
                temperature=0.05,
            )
            # Strip any accidental backtick wrappers Groq might add
            if f"```{language}" in secure_code:
                secure_code = secure_code.split(f"```{language}")[1].split("```")[0].strip()
            elif "```python" in secure_code:
                secure_code = secure_code.split("```python")[1].split("```")[0].strip()
            elif secure_code.startswith("```"):
                secure_code = secure_code.split("```")[1].split("```")[0].strip()
        except Exception as e:
            print(f"[!] Groq secure code step failed: {e}")
            secure_code = f"# ERROR: Groq failed to generate secure code: {e}\n{source_code}"

    return {
        "findings": findings,
        "secure_code": secure_code,
    }



def remediate_code(source_code, language="python"):
    # 1. First Step: Try Local ML Model
    if local_ml_available:
        print("[*] Attempting to analyze code with Local ML Model...")
        ml_result = analyze_with_local_ml(source_code)
        if ml_result:
            print("[*] Local ML Model identified vulnerabilities. Using Groq AI to generate Secure Code...")
            groq_result = call_groq_api(source_code, language)
            
            # Use Local ML findings, but Groq's high-quality secure code
            if "secure_code" in groq_result:
                ml_result["secure_code"] = groq_result["secure_code"]
            else:
                ml_result["secure_code"] = source_code # Fallback
                
            return ml_result
        else:
            print("[*] Local ML Model falling back to Groq AI...")
            
    # 2. Second Step: Fallback to Groq
    return call_groq_api(source_code, language)

