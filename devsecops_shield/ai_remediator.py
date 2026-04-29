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
"""

def _clean_secure_code(result):
    """Defensive cleanup for secure_code field in the JSON response."""
    if "secure_code" in result:
        code = result["secure_code"]
        if "```" in code:
            # Handle potential markdown blocks inside the JSON string
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```javascript" in code:
                code = code.split("```javascript")[1].split("```")[0].strip()
            else:
                code = code.split("```")[1].split("```")[0].strip()
        result["secure_code"] = code
    return result

def remediate_code(source_code, language="python"):
    # --- 1. Try Groq (Fastest, Primary) ---
    if GROQ_API_KEY:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": get_system_prompt(language)},
                {"role": "user", "content": source_code}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return _clean_secure_code(json.loads(content))
            else:
                print(f"[!] Groq Scan Failed ({response.status_code}). Switching to Gemini...")
        except Exception as e:
            print(f"[!] Groq Scan Error: {e}. Switching to Gemini...")

    # --- 2. Gemini Fallback ---
    if gemini_instance:
        try:
            prompt = get_system_prompt(language) + "\n\nSOURCE CODE TO AUDIT:\n" + source_code
            # Use generation_config to force JSON if possible, otherwise rely on prompt
            response = gemini_instance.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            if response and response.text:
                return _clean_secure_code(json.loads(response.text))
        except Exception as e:
            print(f"[!] Gemini Scan Failed: {e}")

    # --- 3. Final Error Response ---
    return {
        "findings": [],
        "secure_code": f"# AI Audit Offline. Verify your API keys in backend/.env."
    }
