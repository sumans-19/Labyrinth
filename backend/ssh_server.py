import paramiko
import threading
import socket
import time
import os
from honeypot import HoneypotSession

# ── Pre-generate host key at module load (fast connections) ─
_HOST_KEY_FILE = os.path.join(os.path.dirname(__file__), "host.key")

def _load_or_generate_host_key():
    if os.path.exists(_HOST_KEY_FILE):
        try:
            return paramiko.RSAKey(filename=_HOST_KEY_FILE)
        except Exception:
            pass
    print("[*] Generating SSH host key (one-time setup)...")
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(_HOST_KEY_FILE)
    print("[*] Host key saved to host.key")
    return key

HOST_KEY = _load_or_generate_host_key()

# ── SSH Server Interface ───────────────────────────────────
class SSHHoneypotServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()
        self.client_ip = "Unknown"

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        return paramiko.AUTH_SUCCESSFUL  # Accept ALL passwords

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_SUCCESSFUL  # Accept ALL keys

    def get_allowed_auths(self, username):
        return "password,publickey"

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_exec_request(self, channel, command):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

# ── Per-connection handler ─────────────────────────────────
def handle_ssh_connection(client_socket, addr, broadcast_callback):
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        transport.set_keepalive(30)

        honeypot_session = HoneypotSession()
        honeypot_session.broadcast_callback = broadcast_callback
        honeypot_session.session_id = f"ssh-{int(time.time())}"
        server = SSHHoneypotServer()
        server.client_ip = addr[0]

        transport.start_server(server=server)

        chan = transport.accept(30)
        if chan is None:
            print(f"[!] SSH: No channel from {addr[0]} (client did not open a shell)")
            return

        # Wait for shell request
        server.event.wait(10)
        chan.settimeout(120)  # 2-minute idle timeout

        print(f"[*] SSH shell opened from {addr[0]}")

        # Broadcast connection event
        broadcast_callback({
            "type": "init",
            "session_id": f"ssh-{int(time.time())}",
            "attacker_ip": addr[0],
            "prompt": honeypot_session.prompt,
            "message": f"🔥 LIVE SSH INTRUSION — Attacker connected from {addr[0]}"
        })

        # Send welcome banner
        chan.send(
            "\r\n\x1b[1;32mWelcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-101-generic x86_64)\x1b[0m\r\n"
            "\r\n * Documentation:  https://help.ubuntu.com\r\n"
            " * Management:     https://landscape.canonical.com\r\n\r\n"
            "Last login: Wed Jan 15 03:47:12 2025 from 10.0.0.1\r\n\r\n"
        )

        # ── Interactive shell loop ─────────────────────────
        while not chan.closed:
            chan.send(f"\r\n{honeypot_session.prompt}")
            cmd = ""

            while True:
                try:
                    data = chan.recv(1)
                    if not data:
                        break
                    ch = data.decode("utf-8", errors="ignore")

                    if ch in ("\r", "\n"):
                        chan.send("\r\n")
                        break
                    elif ch in ("\x03", "\x04"):  # Ctrl+C / Ctrl+D
                        chan.close()
                        return
                    elif ch in ("\x7f", "\x08"):  # Backspace
                        if cmd:
                            cmd = cmd[:-1]
                            chan.send("\b \b")
                    else:
                        cmd += ch
                        chan.send(ch)
                except socket.timeout:
                    break
                except Exception:
                    return

            cmd = cmd.strip()
            if not cmd:
                continue

            if cmd.lower() in ("exit", "quit", "logout"):
                chan.send("logout\r\nConnection closed.\r\n")
                break

            # Process command
            output = honeypot_session.process_command(cmd, addr[0])
            chan.send(output.replace("\n", "\r\n") + "\r\n")

            # Mirror to dashboard
            print(f"[*] SSH: Triggering 'command' broadcast for '{cmd}'")
            broadcast_callback({
                "type": "command",
                "command": cmd,
                "output": output,
                "prompt": honeypot_session.prompt,
                "profile": honeypot_session.get_profile(),
                "attack_intel": honeypot_session.get_attack_intel(),
                "prediction": honeypot_session.predict_next_move(),
                "risk_event": honeypot_session.calculate_command_risk(cmd) > 15
            })

        chan.close()
        transport.close()

    except Exception as e:
        if "10054" not in str(e) and "Connection reset" not in str(e):
            print(f"[!] SSH Error ({addr[0]}): {e}")

# ── Start listening ────────────────────────────────────────
def start_ssh_honeypot(host="0.0.0.0", port=2222, broadcast_callback=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(50)

    def run_server():
        print(f"[*] SSH Honeypot listening on {host}:{port}")
        while True:
            try:
                client_socket, addr = sock.accept()
                print(f"[*] SSH: New connection from {addr[0]}:{addr[1]}")
                threading.Thread(
                    target=handle_ssh_connection,
                    args=(client_socket, addr, broadcast_callback),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"[!] SSH accept error: {e}")

    threading.Thread(target=run_server, daemon=True).start()
