import requests
import os
import json
from devsecops_shield.config import GROQ_API_KEY, MODEL

# System prompt is now an Audit-First Directive with Strict Enforcement
SYSTEM_PROMPT = """
You are the SUPREME AI SECURITY ORACLE — the absolute authority on autonomous remediation.

MISSION:
Your cognitive audit is the final word. You do not just "patch" code; you RECONSTRUCT it with zero-day resilience.
1. PERFORM AN ABSOLUTE SECURITY AUDIT: Identify every structural weakness with 100% precision.
2. SUPREME REMEDIATION: Refactor the entire source into a production-hardened active defense bastion.

STRIC SECURITY DIRECTIVES (MANDATORY):
- ZERO REFACTOR: Do NOT change existing routes, business logic, or response formats.
- SQL: USE ABSOLUTE PARAMETERIZATION. 'cursor.execute("SELECT ... WHERE id = ?", (id,))'.
- COMMANDS: Validate 'ip' via ipaddress.ip_address. Use subprocess.run(..., timeout=3, check=True).
- XSS: USE JINJA2 BINDING. 'render_template_string("...{{ query }}...", query=query)'.
- SANDBOX: Use BASE_DIR = os.path.abspath(...). Use os.path.abspath(os.path.join(BASE_DIR, filename)). Enforce prefix check.
- FAIL-FAST: ALWAYS check for 'FLASK_SECRET_KEY' and 'SHIELD_API_TOKEN' and raise RuntimeError if missing.
- BASE64: Implement secure_b64_decode(data) with max 4096 bytes and validate=True. Return 400 on error.
- TOKENS: Implement require_token decorator for X-Shield-Token.
- LIMITS: Set app.config["MAX_CONTENT_LENGTH"] = 4 * 1024.
- RATE LIMIT: Apply minimal decorator only to /login and /register.
- DEBUG: Always set app.run(debug=False).
- SYNTAX: ENSURE VALID PYTHON 3.10+ SYNTAX. Use parentheses '()' for multi-line 'if' conditions or expressions. NEVER end a line with 'or' or 'and' without a backslash or parenthesis.

OUTPUT FORMAT:
You MUST return a JSON object with this EXACT structure:
{
  "findings": [
    {
      "type": "Vulnerability Name",
      "severity": "CRITICAL/HIGH/MEDIUM",
      "line": 12,
      "description": "Deep technical reasoning on why this is dangerous",
      "snippet": "The exact vulnerable line of code from the source",
      "attack_chain": [
        {
          "stage": 1,
          "phase": "Reconnaissance",
          "actor": "ATTACKER",
          "action": "Short action title (max 8 words)",
          "detail": "What the attacker does or observes at this step (1-2 sentences)",
          "payload": "actual_payload_or_input_used_here",
          "impact": "What breaks or gets exposed as a result"
        },
        {
          "stage": 2,
          "phase": "Exploitation",
          "actor": "SYSTEM",
          "action": "Server processes malicious input",
          "detail": "The vulnerable code path that gets triggered, referencing the snippet",
          "payload": "the SQL/command/path that executes",
          "impact": "Data leaked, command executed, or access gained"
        },
        {
          "stage": 3,
          "phase": "Impact",
          "actor": "RESULT",
          "action": "Full breach achieved",
          "detail": "The final consequence — what the attacker now controls or has stolen",
          "payload": null,
          "impact": "Severity of damage in plain terms"
        }
      ],
      "mitigation": {
        "summary": "One-line explanation of the fix",
        "patched_snippet": "The exact fixed replacement line from secure_code",
        "strategy": "PARAMETERIZE | SANITIZE | VALIDATE | SANDBOX | AUTHENTICATE"
      }
    }
  ],
  "secure_code": "The full hardened python source code"
}
IMPORTANT: attack_chain must always have 3-4 stages. phase must be one of: Reconnaissance, Exploitation, Privilege Escalation, Impact, Exfiltration. actor must be one of: ATTACKER, SYSTEM, RESULT.

"""

def remediate_code(source_code):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": source_code}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"} # Force JSON mode
    }

    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=45)
            if response.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Parse the JSON blob
            result = json.loads(content)
            
            # Defensive cleanup for secure_code
            if "secure_code" in result:
                code = result["secure_code"]
                if "```python" in code:
                    code = code.split("```python")[1].split("```")[0].strip()
                elif "```" in code:
                    code = code.split("```")[1].split("```")[0].strip()
                result["secure_code"] = code
                
            return result
            
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "findings": [],
                    "secure_code": f"# ERROR: AI Audit failed: {str(e)}"
                }
            time.sleep(5)
    
    return {
        "findings": [],
        "secure_code": "# ERROR: AI Audit failed: Max retries exceeded (Rate Limit)"
    }
