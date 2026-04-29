import os
import sys
import json
import logging

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from devsecops_shield.analyzer import scan

code = """
from flask import Flask, request, send_file, render_template_string
import os
import subprocess

app = Flask(__name__)
BASE_DIR = os.path.abspath('files')
os.makedirs(BASE_DIR, exist_ok=True)

@app.route('/')
def home():
    return 'Home'

@app.route('/echo')
def echo():
    msg = request.args.get('msg', '')
    return render_template_string('<h3>You said: {{ msg | e }}</h3>')

@app.route('/read')
def read_file():
    fname = request.args.get('file', '')
    path = os.path.abspath(os.path.join(BASE_DIR, fname))
    if not os.path.relpath(path, start=BASE_DIR).startswith('.'): 
        return 'Invalid file path'
    return send_file(path)

@app.route('/exec')
def exec_cmd():
    cmd = request.args.get('cmd', '')
    output = subprocess.run(cmd.split(), capture_output=True, text=True, shell=False)
    return f'<pre>{output.stdout}</pre>'

if __name__ == '__main__':
    app.run(debug=True)
"""

res = scan(code)
print(json.dumps(res, indent=2))
