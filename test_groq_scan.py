import sys
sys.path.insert(0, 'd:/Labyrinth')
sys.path.insert(0, 'd:/Labyrinth/devsecops_shield')

import requests
from config import GROQ_API_KEY, MODEL

test_code = "import sqlite3\ndef get_user(username):\n    conn = sqlite3.connect('users.db')\n    query = \"SELECT * FROM users WHERE username = '\" + username + \"'\"\n    conn.execute(query)"

findings_system = """You are a security auditor. Analyze the Python code for REAL exploitable vulnerabilities.
Return ONLY a valid JSON object:
{"findings": [{"type": "Vulnerability Name", "severity": "CRITICAL", "line": 1, "description": "why", "snippet": "bad line", "attack_chain": [], "mitigation": {"summary": "fix", "patched_snippet": "", "strategy": "PARAMETERIZE"}}]}
If secure, return: {"findings": []}"""

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": findings_system},
        {"role": "user", "content": test_code}
    ],
    "response_format": {"type": "json_object"},
    "max_tokens": 1024,
    "temperature": 0.1
}

print(f"[*] Testing model: {MODEL}")
print(f"[*] Key prefix: {GROQ_API_KEY[:8]}...")

r = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
    json=payload,
    timeout=30
)

print(f"[*] Status: {r.status_code}")
print(f"[*] Response:\n{r.text[:1200]}")

if r.status_code == 200:
    content = r.json()["choices"][0]["message"]["content"]
    print(f"\n[+] Content:\n{content}")
