import os
import sys
import json
import logging

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from devsecops_shield.ai_remediator import call_groq_api

code = """
from flask import Flask, request, send_file, render_template_string
import os

app = Flask(__name__)
BASE_DIR = os.path.abspath("files")
os.makedirs(BASE_DIR, exist_ok=True)

@app.route("/")
def home():
    return "Home"

@app.route("/echo")
def echo():
    msg = request.args.get("msg", "")
    return render_template_string(f"<h3>You said: {msg}</h3>")

@app.route("/read")
def read_file():
    fname = request.args.get("file", "")
    path = os.path.join(BASE_DIR, fname)  # no validation
    return send_file(path)

@app.route("/exec")
def exec_cmd():
    cmd = request.args.get("cmd", "")
    output = os.popen(cmd).read()
    return f"<pre>{output}</pre>"

if __name__ == "__main__":
    app.run(debug=True)
"""

res = call_groq_api(code)
print(json.dumps(res, indent=2))
