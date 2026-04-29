import sys
sys.path.append('.')
sys.path.append('./backend')
from backend.scanner import scan_code
from devsecops_shield.ai_remediator import call_groq_api
from devsecops_shield.validator import validate_secure
import json

code = """# INTENTIONALLY VULNERABLE
from flask import Flask, request, send_file, render_template_string
import os

app = Flask(__name__)
BASE_DIR = os.path.abspath("files")
os.makedirs(BASE_DIR, exist_ok=True)

@app.route("/")
def home():
    return "<h2>Mini Vulnerable App</h2>"

@app.route("/echo")
def echo():
    msg = request.args.get("msg", "")
    return render_template_string(f"<h3>You said: {msg}</h3>")

@app.route("/read")
def read_file():
    fname = request.args.get("file", "")
    path = os.path.join(BASE_DIR, fname)
    return send_file(path)

@app.route("/exec")
def exec_cmd():
    cmd = request.args.get("cmd", "")
    output = os.popen(cmd).read()
    return f"<pre>{output}</pre>"

if __name__ == "__main__":
    app.run(debug=True)
"""

print("=== Step 1: Calling Groq AI for secure code ===")
groq_result = call_groq_api(code)
secure_code = groq_result.get("secure_code", "")
print("Groq secure_code (first 300):", repr(secure_code[:300]))
print()

print("=== Step 2: Validating Groq secure code ===")
is_valid = validate_secure(secure_code)
print("Is valid:", is_valid)
print()

from devsecops_shield.analyzer import scan
issues = scan(secure_code)
print("AST scanner issues on secure code:", json.dumps(issues, indent=2))
