import paramiko
import threading
import json
import time
import socket
from honeypot import HoneypotSession

class SSHHoneypotServer(paramiko.ServerInterface):
    def __init__(self, session, broadcast_callback):
        self.event = threading.Event()
        self.session = session
        self.broadcast_callback = broadcast_callback
        self.client_ip = "Unknown"

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # Accept all passwords for maximum deception
        return paramiko.AUTH_SUCCESSFUL

    def get_allowed_auths(self, username):
        return "password"

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

import os

def handle_ssh_connection(client, addr, broadcast_callback):
    try:
        transport = paramiko.Transport(client)
        
        # Load or generate a persistent host key
        key_file = "host.key"
        if os.path.exists(key_file):
            host_key = paramiko.RSAKey(filename=key_file)
        else:
            host_key = paramiko.RSAKey.generate(2048)
            host_key.write_private_key_file(key_file)
            
        transport.add_server_key(host_key)
        
        session = HoneypotSession()
        server = SSHHoneypotServer(session, broadcast_callback)
        server.client_ip = addr[0]
        
        transport.start_server(server=server)
        chan = transport.accept(20)
        if chan is None:
            return

        chan.settimeout(None)
        
        # Broadcast connection start using the relay
        print(f"[*] SSH: Triggering 'init' broadcast for {addr[0]}")
        broadcast_callback({
            "type": "init",
            "session_id": f"ssh-{int(time.time())}",
            "attacker_ip": addr[0],
            "prompt": session.prompt,
            "message": f"🔥 LIVE SSH INTRUSION — Attacker connected from {addr[0]}"
        })

        chan.send(f"\r\nWelcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-101-generic x86_64)\r\n\r\n")
        
        while not chan.closed:
            chan.send(f"\r\n{session.prompt}")
            cmd = ""
            while True:
                try:
                    data = chan.recv(1)
                    if not data:
                        break
                    char = data.decode("utf-8", errors="ignore")
                    
                    if char == "\r" or char == "\n":
                        chan.send("\r\n")
                        break
                    elif char == "\x03" or char == "\x04": # Ctrl+C or Ctrl+D
                        chan.close()
                        return
                    elif char == "\x7f" or char == "\x08": # Backspace or Delete
                        if len(cmd) > 0:
                            cmd = cmd[:-1]
                            chan.send("\b \b")
                    else:
                        cmd += char
                        chan.send(char)
                except:
                    break
            
            cmd = cmd.strip()
            if cmd.lower() in ["exit", "quit"]:
                chan.send("logout\r\nConnection closed.\r\n")
                break
                
            if cmd:
                output = session.process_command(cmd)
                chan.send(output.replace("\n", "\r\n") + "\r\n")
                
                print(f"[*] SSH: Triggering 'command' broadcast for '{cmd}'")
                broadcast_callback({
                    "type": "command",
                    "command": cmd,
                    "output": output,
                    "prompt": session.prompt,
                    "profile": session.get_profile(),
                    "attack_intel": session.get_attack_intel(),
                    "prediction": session.predict_next_move(),
                    "risk_event": session.calculate_command_risk(cmd) > 15
                })
        
        chan.close()
        transport.close()
    except Exception as e:
        if "10054" not in str(e):
            print(f"[!] SSH Error: {e}")

def start_ssh_honeypot(host="0.0.0.0", port=2222, broadcast_callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(100)
    
    def run_server():
        print(f"[*] SSH Honeypot listening on {host}:{port}")
        while True:
            try:
                client, addr = sock.accept()
                threading.Thread(
                    target=handle_ssh_connection, 
                    args=(client, addr, broadcast_callback), 
                    daemon=True
                ).start()
            except Exception as e:
                print(f"[!] socket error: {e}")
            
    threading.Thread(target=run_server, daemon=True).start()
