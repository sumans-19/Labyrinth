import os
import requests
import json
import logging
import os
from dotenv import load_dotenv

# Find .env relative to this file's project structure (d:\Labyrinth\backend\.env)
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, 'backend', '.env')
load_dotenv(dotenv_path=env_path, override=True)

class GroqClient:
    """
    Autonomous Report Generator for DevSecOps Shield.
    """
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if self.api_key:
            print(f"DEBUG: GroqClient using key starting with: {self.api_key[:10]}...")
        else:
            print("DEBUG: GroqClient: No API key found in environment!")
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.model = model or "llama-3.3-70b-versatile"

    def generate_autonomous_report(self, findings, explanation_context, secure_code, original_code):
        prompt = f"""
You are DEVSECOPS SHIELD — an enterprise-grade autonomous DevSecOps remediation engine.

AUDIT FINDINGS (Deterministic):
{findings}

SECURE REFACTORED CODE (Structural):
{secure_code}

ORIGINAL CODE:
{original_code}

Your mission:
1. Perform deep static analysis on the provided source code.
2. Detect all security vulnerabilities including: SQLi (CWE-89), CMDi (CWE-78), RCE (CWE-94), Deserialization (CWE-502), XSS (CWE-79), Path Traversal (CWE-73), Secrets (CWE-798), Debug Mode, Missing Input Validation, Missing Auth, Unsafe File Access, Missing Rate Limiting, Missing CSRF, Missing Secure Headers, Weak Error Handling.

3. Perform pseudo-taint analysis:
   - Track request.args, request.form, request.data, and variable propagation.
   - If tainted input reaches dangerous sinks (exec, eval, os.system, subprocess, pickle.loads, raw SQL, open, render_template_string), mark CRITICAL.

4. Generate a structured output with:

SECTION 1: Vulnerability Report (JSON array)
Each issue: CWE ID, Severity (LOW/HIGH/CRITICAL), Line, Snippet, Explanation, Attack vector.

SECTION 2: Risk Score Before Fix (0-100)

SECTION 3: Fully Hardened Secure Code
Requirements:
- No dangerous sinks. SQL must use parameterized queries.
- No exec/eval/pickle on untrusted input.
- File access must use sandboxed BASE_DIR.
- IP addresses validated via 'ipaddress' module.
- Secrets from ENV variables. Debug disabled.
- Add: Rate limiting, CSRF protection, secure headers, global error handler, input length validation, request size limit.
- Remove unused insecure imports (pickle, etc). Preserve functionality where safe.

SECTION 4: Risk Score After Fix (0-100)

SECTION 5: Hardening Enhancements Added
List every added defensive control and why it improves resilience.

CRITICAL RULE:
If ANY dangerous sink remains in the final code, you MUST reject your own output and regenerate.
Do not hallucinate partial fixes. Code must be syntactically valid and production-ready.
"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a Senior Security Architect. Output only the requested sections. Be technical and precise."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"GROQ_ERROR_{response.status_code}: {response.text}"
        except Exception as e:
            logging.error(f"Groq Client Error: {e}")
            return "ERROR: AI Remediation Layer Unreachable."

    def generate(self, prompt, json_format=False):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        if json_format:
            payload["response_format"] = {"type": "json_object"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                if json_format:
                    return json.loads(content)
                return content
            else:
                logging.error(f"Groq API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logging.error(f"Groq Client Error: {e}")
            return None
