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
You MUST return a JSON object. If the code is perfectly secure with zero vulnerabilities, return an empty array for "findings": "findings": []. Otherwise:
{{
  "findings": [
    {{
      "type": "Vulnerability Name",
      "severity": "CRITICAL/HIGH/MEDIUM",
      "line": 12,
      "description": "Deep reasoning on the vulnerability",
      "snippet": "Vulnerable code snippet"
    }}
  ],
  "secure_code": "The full hardened {language} source code"
}}
"""

def remediate_code(source_code, language="python"):
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
