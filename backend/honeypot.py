import random
import time
import os
import json
import sys
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import mm
import io
from datetime import datetime

# Ensure project root is in path for shield_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Groq AI Configuration (Honeypot Emulation) ─────────
from shield_engine.llm.groq_client import GroqClient
shield_ai = GroqClient(model="llama-3.3-70b-versatile")


# ── MITRE ATT&CK Kill Chain Mapping ──────────────────
KILL_CHAIN_PHASES = [
    {"id": "recon", "name": "Reconnaissance", "color": "#3b82f6"},
    {"id": "initial_access", "name": "Initial Access", "color": "#8b5cf6"},
    {"id": "execution", "name": "Execution", "color": "#06b6d4"},
    {"id": "persistence", "name": "Persistence", "color": "#f59e0b"},
    {"id": "priv_esc", "name": "Privilege Escalation", "color": "#ef4444"},
    {"id": "credential_access", "name": "Credential Access", "color": "#ec4899"},
    {"id": "collection", "name": "Collection & Exfiltration", "color": "#ef4444"},
]

# Maps command patterns → (ATT&CK Technique ID, Name, Kill Chain Phase)
MITRE_ATTACK_MAP = [
    # Reconnaissance
    (["whoami", "id", "hostname", "uname"], "T1033", "System Owner/User Discovery", "recon"),
    (["ifconfig", "ip addr", "ipconfig"], "T1016", "System Network Configuration Discovery", "recon"),
    (["ps aux", "tasklist"], "T1057", "Process Discovery", "recon"),
    (["netstat", "ss -"], "T1049", "System Network Connections Discovery", "recon"),
    (["ls ", "dir ", "find "], "T1083", "File and Directory Discovery", "recon"),
    (["cat /etc/passwd", "cat /etc/group"], "T1087", "Account Discovery", "recon"),
    (["systeminfo", "uname -a"], "T1082", "System Information Discovery", "recon"),
    (["pwd"], "T1083", "File and Directory Discovery", "recon"),

    # Execution
    (["python -c", "python3 -c", "bash -c", "sh -c"], "T1059", "Command and Scripting Interpreter", "execution"),
    (["wget ", "curl "], "T1105", "Ingress Tool Transfer", "execution"),
    (["chmod +x", "chmod 777"], "T1222", "File and Directory Permissions Modification", "execution"),

    # Persistence
    (["crontab", "/etc/cron"], "T1053", "Scheduled Task/Job", "persistence"),
    ([".bashrc", ".profile", ".bash_profile"], "T1546", "Event Triggered Execution", "persistence"),
    (["useradd", "adduser", "net user"], "T1136", "Create Account", "persistence"),

    # Privilege Escalation
    (["sudo", "su ", "runas"], "T1548", "Abuse Elevation Control Mechanism", "priv_esc"),
    (["cat /etc/shadow", "hashdump"], "T1003", "OS Credential Dumping", "priv_esc"),
    (["chmod u+s", "setuid"], "T1548.001", "Setuid and Setgid", "priv_esc"),

    # Credential Access
    (["id_rsa", "ssh key", ".ssh/"], "T1552", "Unsecured Credentials", "credential_access"),
    (["aws_credentials", "credentials.bak"], "T1552.001", "Credentials In Files", "credential_access"),
    (["deploy_keys", "prod.env", ".env"], "T1552.001", "Credentials In Files", "credential_access"),
    (["passwords", "password"], "T1552", "Unsecured Credentials", "credential_access"),

    # Collection & Exfiltration
    (["employee_records", "budget", "financial"], "T1005", "Data from Local System", "collection"),
    (["tar ", "zip ", "gzip", "7z"], "T1560", "Archive Collected Data", "collection"),
    (["scp ", "nc ", "netcat", "/dev/tcp"], "T1041", "Exfiltration Over C2 Channel", "collection"),
    (["base64", "xxd"], "T1132", "Data Encoding", "collection"),
    (["db_dump", "sql.gz", ".sql"], "T1005", "Data from Local System", "collection"),
]

# Markov-like prediction transitions: phase → likely next phases with probabilities
PHASE_TRANSITIONS = {
    "recon": [
        ("credential_access", 0.35, "Attempt to access stored credentials"),
        ("execution", 0.30, "Execute scripts or download tools"),
        ("priv_esc", 0.20, "Attempt privilege escalation"),
        ("collection", 0.15, "Collect sensitive data"),
    ],
    "initial_access": [
        ("recon", 0.50, "Enumerate the system environment"),
        ("execution", 0.30, "Execute payloads"),
        ("persistence", 0.20, "Establish persistence"),
    ],
    "execution": [
        ("persistence", 0.30, "Install backdoor or scheduled task"),
        ("priv_esc", 0.30, "Escalate privileges"),
        ("credential_access", 0.25, "Harvest credentials"),
        ("collection", 0.15, "Begin data collection"),
    ],
    "persistence": [
        ("priv_esc", 0.40, "Attempt privilege escalation"),
        ("credential_access", 0.35, "Harvest credentials for lateral movement"),
        ("collection", 0.25, "Collect and stage data"),
    ],
    "priv_esc": [
        ("credential_access", 0.45, "Dump credentials with elevated privileges"),
        ("collection", 0.30, "Access restricted data"),
        ("persistence", 0.25, "Establish persistent elevated access"),
    ],
    "credential_access": [
        ("collection", 0.50, "Use credentials to access sensitive data"),
        ("priv_esc", 0.25, "Use credentials for privilege escalation"),
        ("execution", 0.25, "Use credentials to execute further attacks"),
    ],
    "collection": [
        ("collection", 0.50, "Continue harvesting more data"),
        ("credential_access", 0.25, "Look for more credentials"),
        ("recon", 0.25, "Search for additional targets"),
    ],
}


def _ask_ai(command: str, mode: str, cwd: str) -> str | None:
    """
    Generate a realistic terminal response.
    Uses local Ollama (Llama-3.1) for high-speed, zero-quota emulation.
    """
    cmd_base = command.strip().split()[0] if command.strip() else ""
    
    # 1. Deterministic Rule Book (High Speed)
    if cmd_base in ["ls", "dir", "cd", "pwd", "whoami", "id", "chmod"]:
        return None # Let standard logic handle these
    
    if cmd_base == "netstat" or cmd_base == "ss":
        return "Active Internet connections (only servers)\nProto Recv-Q Send-Q Local Address           Foreign Address         State      \ntcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN     "

    # 2. Local AI Generation
    try:
        os_desc = "Ubuntu 20.04" if mode == "ubuntu" else "Windows Server"
        # Enhanced prompt for more realistic context handling
        system_context = f"You are a realistic {os_desc} terminal."
        if command.strip().startswith("sudo"):
            system_context += " The user is running this with SUDO privileges. Act as root."
        
        prompt = f"SYSTEM: {system_context} CWD: {cwd}. Respond with ONLY the terminal output to: {command}"
        response = shield_ai.generate(prompt)
        if response:
            return response.replace("```", "").strip()
    except Exception as e:
        logging.error(f"AI Generation Error: {e}")
        pass # Silent fallback

    return None

# ── Fake filesystem ──────────────────────────────────
UBUNTU_FS = {
    "/": ["bin", "boot", "dev", "etc", "home", "lib", "media", "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"],
    "/etc": ["passwd", "shadow", "hostname", "hosts", "resolv.conf", "ssh", "nginx", "crontab", "fstab", "group"],
    "/home": ["sysadmin", "deploy", "jenkins"],
    "/home/sysadmin": ["Documents", "Downloads", ".ssh", ".bash_history", ".bashrc", ".profile"],
    "/home/sysadmin/Documents": ["Q3_Financials.pdf", "passwords.xlsx", "network_diagram.png", "budget_2024.csv", "employee_records.csv", "aws_credentials.bak", "deploy_keys.txt", "internal_memo.docx"],
    "/home/sysadmin/Downloads": ["setup.sh", "vpn_config.ovpn", "meeting_notes.txt"],
    "/home/sysadmin/.ssh": ["id_rsa", "id_rsa.pub", "authorized_keys", "known_hosts", "config"],
    "/home/deploy": [".bash_history", "deploy.sh", "staging.env", "prod.env"],
    "/root": [".bash_history", ".bashrc", ".ssh", "maintenance.sh"],
    "/var": ["log", "www", "lib", "cache", "run"],
    "/var/log": ["syslog", "auth.log", "kern.log", "nginx", "cron.log", "fail2ban.log"],
    "/var/www": ["html"],
    "/var/www/html": ["index.html", "app.js", "config.php", ".env"],
    "/tmp": ["sess_a8f32b", "upload_tmp", ".X11-unix"],
    "/opt": ["scripts", "backups"],
    "/opt/backups": ["db_dump_2024.sql.gz", "full_backup_jan.tar.gz"],
}

WINDOWS_FS = {
    "C:\\": ["Users", "Windows", "Program Files", "Program Files (x86)", "inetpub", "temp"],
    "C:\\Users": ["Administrator", "svc_account", "Public"],
    "C:\\Users\\Administrator": ["Desktop", "Documents", "Downloads", ".ssh"],
    "C:\\Users\\Administrator\\Desktop": ["passwords.txt", "vpn_config.ovpn", "deploy.ps1", "budget.xlsx"],
    "C:\\Users\\Administrator\\Documents": ["Q3_Financials.pdf", "employee_records.csv", "internal_memo.docx"],
    "C:\\inetpub": ["wwwroot", "logs"],
    "C:\\inetpub\\wwwroot": ["index.html", "web.config", "app_data"],
}

IOT_FS = {
    "/": ["bin", "etc", "dev", "tmp", "var", "usr", "sys", "proc", "mnt"],
    "/etc": ["config", "passwd", "shadow", "firmware.bin", "network.conf", "init.d"],
    "/var": ["log", "data"],
    "/var/data": ["sensor_log.csv", "telemetry.db", "device_id.txt"],
    "/tmp": ["update.bin", "core_dump"],
}

# ── Fake file contents ───────────────────────────────
FILE_CONTENTS = {
    "/etc/passwd": """root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
sysadmin:x:1000:1000:System Admin,,,:/home/sysadmin:/bin/bash
deploy:x:1001:1001:Deploy User,,,:/home/deploy:/bin/bash
jenkins:x:1002:1002:Jenkins CI,,,:/home/jenkins:/bin/bash""",

    "/home/sysadmin/.ssh/id_rsa": """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA3dKS9aKX7q0J1F0rT8t5X2HONEY+TOKEN+FAKE+KEY
kD8nFz6Q2Rj4hW8kP9lJvNmC3bK7gY5sD1fH2jL0mN4pR6tV8wX0yB2
FAKE+HONEYPOT+GENERATED+RSA+KEY+DO+NOT+USE+IN+PRODUCT
qW3eR5tY7uI9oP0aS2dF4gH6jK8lZ1xC3vB5nM7QW9ER0TY1UI2OP3
-----END RSA PRIVATE KEY-----""",

    "/home/sysadmin/Documents/budget_2024.csv": """Department,Q1,Q2,Q3,Q4,Total
Engineering,1250000,1340000,1420000,1500000,5510000
Marketing,800000,850000,920000,980000,3550000
Sales,650000,700000,750000,800000,2900000
Operations,450000,480000,510000,540000,1980000
HR,320000,340000,360000,380000,1400000
Finance,280000,300000,320000,340000,1240000""",

    "/home/sysadmin/Documents/aws_credentials.bak": """[default]
aws_access_key_id = AKIAIOSFODNN7HONEYTOKEN
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYHONEYTOKEN99
region = us-east-1

[production]
aws_access_key_id = AKIAI44QH8DHBHONEY002
aws_secret_access_key = je7MtGbClwBF/2Zp9Utk/h3yCo8nvbHONEYTOKEN42
region = us-west-2""",

    "/home/sysadmin/Documents/employee_records.csv": """ID,Name,Role,Email,Salary,SSN
1001,Sarah Chen,VP Engineering,schen@acme-corp.internal,185000,XXX-XX-7234
1002,Mike Rodriguez,Lead DevOps,mrodriguez@acme-corp.internal,142000,XXX-XX-8891
1003,Priya Sharma,Security Analyst,psharma@acme-corp.internal,128000,XXX-XX-4412
1004,James Wilson,DBA,jwilson@acme-corp.internal,135000,XXX-XX-6673
1005,Emily Tanaka,Frontend Lead,etanaka@acme-corp.internal,138000,XXX-XX-2290""",

    "/home/deploy/prod.env": """DATABASE_URL=postgresql://prod_user:Pr0d_P@ss2024!@db-prod.acme-internal:5432/acme_prod
REDIS_URL=redis://:R3d1s_S3cr3t@cache-prod.acme-internal:6379/0
JWT_SECRET=hny_j8K2mP4qR7sT0vW3xY6zA9bC1dE5fG
AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
STRIPE_SECRET_KEY=sk_live_honeytoken_51Hb3kZ9
SMTP_PASSWORD=Em@1l_S3nd3r_2024!""",

    "/var/www/html/.env": """APP_NAME=AcmeCorp-Internal
APP_ENV=production
APP_KEY=base64:hOnEyToKeN/fake+key+do+not+use==
APP_DEBUG=false
DB_HOST=db-prod.acme-internal
DB_DATABASE=acme_production
DB_USERNAME=webapp_user
DB_PASSWORD=W3b@pp_Db_2024!""",

    "/home/sysadmin/Documents/deploy_keys.txt": """=== DEPLOYMENT ACCESS KEYS ===
Updated: 2024-01-15

Production Server: ssh deploy@10.0.1.50 -i /opt/keys/prod.pem
Staging Server:    ssh deploy@10.0.2.50 -i /opt/keys/staging.pem
Jenkins:           admin / J3nk1ns_Adm1n_2024!
Grafana:           admin / Gr@f@n@_M0n1t0r!
ArgoCD:            admin / @rg0_D3pl0y_K3y""",

    "/opt/backups/db_dump_2024.sql.gz": "[BINARY DATA — gzip compressed SQL dump, 234MB]",
}

# ── Fake command outputs ─────────────────────────────

def _ls_la(path: str, fs: dict) -> str:
    contents = fs.get(path, [])
    if not contents:
        return f"ls: cannot access '{path}': No such file or directory"
    lines = [f"total {len(contents) * 4}"]
    for item in contents:
        is_dir = (path.rstrip("/") + "/" + item) in fs or (path.rstrip("/") + "/" + item).replace("/", "\\") in fs
        perms = "drwxr-xr-x" if is_dir else "-rw-r--r--"
        size = random.randint(100, 99000) if not is_dir else 4096
        lines.append(f"{perms}  1 root root {size:>8} Jan {random.randint(1,28):>2} {random.randint(0,23):02}:{random.randint(0,59):02} {item}")
    return "\n".join(lines)


def _cat(path: str) -> str:
    if path in FILE_CONTENTS:
        return FILE_CONTENTS[path]
    return f"cat: {path}: No such file or directory"


class HoneypotSession:
    """In-memory state for one attacker session."""

    def __init__(self, mode: str = "ubuntu"):
        self.mode = mode
        self.cwd = "/" if mode != "windows" else "C:\\"
        self.history: list[dict] = []
        self.frustration = 0
        self.commands_run = 0
        self.start_time = time.time()
        self.dave_triggered = False
        self.isolated = False
        self.reverse_hack_intel = self._generate_reverse_hack_intel()

    def _generate_reverse_hack_intel(self) -> dict:
        """Simulate extracting data from the attacker's machine."""
        os_options = ["Windows 11 Pro", "Kali Linux 2024.1", "macOS Sonoma", "Ubuntu 22.04 LTS"]
        device_names = ["HACK-LAPTOP-X9", "DRAGON-PC", "GHOST-ZBOOK", "ANONYMOUS-MACHINE"]
        
        return {
            "device_name": random.choice(device_names),
            "os": random.choice(os_options),
            "mac_address": f"{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}",
            "browser": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "cpu_arch": random.choice(["x86_64", "ARM64"]),
            "stolen_data_clues": [
                "Found local .env with AWS keys",
                "Chrome cookies for banking.com identified",
                "Slack credentials located in /var/tmp",
                "History shows attack on local-banking-site"
            ]
        }

    @property
    def fs(self):
        if self.mode == "windows":
            return WINDOWS_FS
        if self.mode == "iot":
            return IOT_FS
        return UBUNTU_FS

    @property
    def prompt(self):
        if self.mode == "windows":
            return f"C:\\Users\\Administrator>"
        if self.mode == "iot":
            return f"iot-device:{self.cwd}# "
        return f"sysadmin@acme-prod:{self.cwd}$ "

    def process_command(self, cmd: str) -> str:
        """Process a shell command and return mock output."""
        self.commands_run += 1
        cmd = cmd.strip()
        self.history.append({"cmd": cmd, "time": time.time()})

        # Frustration bumps for suspicious commands
        sus = ["cat /etc/shadow", "sudo", "chmod", "wget", "curl", "nc ", "nmap", "hydra"]
        if any(s in cmd for s in sus):
            self.frustration = min(100, self.frustration + random.randint(5, 15))

        # ── NAVIGATION LOGIC (Maintain CWD state) ──
        if cmd.startswith("cd "):
            target = cmd[3:].strip()
            # Simple state tracking for the prompt, but the OUTPUT will still be AI
            if target == "..":
                if self.mode == "windows":
                    if len(self.cwd) > 3: # C:\
                        self.cwd = self.cwd.rstrip("\\").rsplit("\\", 1)[0] + "\\"
                else:
                    parts = self.cwd.rstrip("/").rsplit("/", 1)
                    self.cwd = parts[0] if parts[0] else "/"
            elif not target.startswith("-"): # Don't track flags
                if self.mode == "windows":
                    if ":" in target: self.cwd = target
                    else: self.cwd = self.cwd.rstrip("\\") + "\\" + target + "\\"
                else:
                    if target.startswith("/"): self.cwd = target
                    else: self.cwd = self.cwd.rstrip("/") + "/" + target

        # ── GEMINI GENERATION (The "Answer") ──
        ai_response = _ask_ai(cmd, self.mode, self.cwd)
        if ai_response:
            # Handle clear command locally for better UX if AI doesn't
            if cmd.lower() == "clear":
                return "\033[H\033[2J" 
            return ai_response

        # Fallback to legacy modes if AI fails
        if self.mode == "windows":
            return self._windows_cmd(cmd)
        if self.mode == "iot":
            return self._iot_cmd(cmd)
        return self._ubuntu_cmd(cmd)

    def _ubuntu_cmd(self, cmd: str) -> str:
        if cmd == "whoami":
            return "sysadmin"
        if cmd == "id":
            return "uid=1000(sysadmin) gid=1000(sysadmin) groups=1000(sysadmin),27(sudo),33(www-data)"
        if cmd == "hostname":
            return "acme-prod-web01"
        if cmd == "uname -a":
            return "Linux acme-prod-web01 5.4.0-150-generic #167-Ubuntu SMP Mon Jan 16 12:42:35 UTC 2024 x86_64 GNU/Linux"
        if cmd == "pwd":
            return self.cwd
        if cmd.startswith("cd "):
            target = cmd[3:].strip()
            if target == "..":
                parts = self.cwd.rstrip("/").rsplit("/", 1)
                self.cwd = parts[0] if parts[0] else "/"
            elif target.startswith("/"):
                if target.rstrip("/") in self.fs or target in self.fs:
                    self.cwd = target.rstrip("/") or "/"
                else:
                    return f"-bash: cd: {target}: No such file or directory"
            else:
                new = self.cwd.rstrip("/") + "/" + target
                if new in self.fs:
                    self.cwd = new
                else:
                    return f"-bash: cd: {target}: No such file or directory"
            return ""
        if cmd.startswith("ls"):
            path = self.cwd
            parts = cmd.split()
            flags = [p for p in parts[1:] if p.startswith("-")]
            args = [p for p in parts[1:] if not p.startswith("-")]
            if args:
                path = args[0] if args[0].startswith("/") else self.cwd.rstrip("/") + "/" + args[0]
            if any("-l" in f for f in flags) or "-la" in cmd:
                return _ls_la(path, self.fs)
            contents = self.fs.get(path, [])
            if not contents:
                return f"ls: cannot access '{path}': No such file or directory"
            return "  ".join(contents)
        if cmd.startswith("cat "):
            fpath = cmd[4:].strip()
            if not fpath.startswith("/"):
                fpath = self.cwd.rstrip("/") + "/" + fpath
            return _cat(fpath)
        if cmd == "ifconfig" or cmd == "ip addr":
            return """eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.1.42  netmask 255.255.255.0  broadcast 10.0.1.255
        inet6 fe80::a00:27ff:fe8e:4e62  prefixlen 64  scopeid 0x20<link>
        ether 08:00:27:8e:4e:62  txqueuelen 1000  (Ethernet)"""
        if cmd == "netstat -tlnp" or cmd == "ss -tlnp":
            return """State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN  0       128     0.0.0.0:22           0.0.0.0:*          sshd
LISTEN  0       128     0.0.0.0:80           0.0.0.0:*          nginx
LISTEN  0       128     0.0.0.0:443          0.0.0.0:*          nginx
LISTEN  0       128     127.0.0.1:5432       0.0.0.0:*          postgres
LISTEN  0       128     127.0.0.1:6379       0.0.0.0:*          redis-server"""
        if cmd.startswith("cat /etc/shadow"):
            self.frustration = min(100, self.frustration + 10)
            return f"bash: permission denied"

        # ── EDITOR MOCKS (Nano / Gedit) ──
        if cmd.startswith("nano "):
            filename = cmd[5:].strip() or "new_file"
            upper = "  GNU nano 6.2".ljust(30) + filename.center(20) + "Modified".rjust(30)
            content = "\n" * 10 + "      [ File is empty or protected ]" + "\n" * 10
            lower = "^G Get Help  ^O Write Out  ^W Where Is  ^K Cut Text    ^J Justify    ^C Cur Pos\n^X Exit      ^R Read File  ^\\ Replace   ^U Uncut Text  ^T To Linter  ^_ Go To Line"
            return f"\x1b[7m{upper}\x1b[0m\n{content}\n\x1b[7m{lower}\x1b[0m"

        if cmd.startswith("gedit "):
            return f"Opening gedit window on display :0.0...\n(gedit:14230): Gtk-WARNING **: 10:25:35.123: cannot open display: :0.0\nTry: ssh -X user@host to enable X11 forwarding."

        if cmd == "ps aux":
            return """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 225816  9428 ?        Ss   Jan15   0:03 /sbin/init
root       412  0.0  0.1  72308  6072 ?        Ss   Jan15   0:00 /usr/sbin/sshd
www-data  1024  0.0  0.5 345612 22480 ?        S    Jan15   0:12 nginx: worker
postgres  1180  0.0  0.8 394520 33284 ?        Ss   Jan15   0:45 postgres
sysadmin 14230  0.0  0.1  21464  5024 pts/0    Ss   10:23   0:00 -bash
sysadmin 14285  0.0  0.0  38376  3408 pts/0    R+   10:25   0:00 ps aux"""
        if cmd == "history":
            return "\n".join([f"  {i+1}  {h['cmd']}" for i, h in enumerate(self.history[-20:])])

        # ── ADDITIONAL TOOLS (Mocked for realism) ──
        if cmd.startswith("chmod "):
            parts = cmd.split()
            if len(parts) < 3:
                return "chmod: missing operand"
            return "" # Silent success

        if cmd.startswith("chown "):
            parts = cmd.split()
            if len(parts) < 3:
                return "chown: missing operand"
            return "" # Silent success

        if cmd.startswith("stat "):
            fpath = cmd[5:].strip()
            if not fpath.startswith("/"):
                fpath = self.cwd.rstrip("/") + "/" + fpath
            if fpath in self.fs or fpath in FILE_CONTENTS:
                return f"  File: {fpath}\n  Size: {random.randint(100, 5000)} \tBlocks: 8          IO Block: 4096   regular file\nDevice: 801h/2049d\tInode: {random.randint(100000, 999999)}    Links: 1\nAccess: (0644/-rw-r----)  Uid: ( 1000/sysadmin)   Gid: ( 1000/sysadmin)"
            return f"stat: cannot stat '{fpath}': No such file or directory"

        if cmd == "lscpu":
            return """Architecture:            x86_64
  CPU op-mode(s):        32-bit, 64-bit
  Address sizes:         39 bits physical, 48 bits virtual
  Byte Order:            Little Endian
CPU(s):                  4
  On-line CPU(s) list:   0-3
Vendor ID:               GenuineIntel
  Model name:            Intel(R) Xeon(R) CPU @ 2.20GHz"""

        if cmd.startswith("apt "):
            return "E: Could not open lock file /var/lib/dpkg/lock-frontend - open (13: Permission denied)\nE: Unable to acquire the dpkg frontend lock (/var/lib/dpkg/lock-frontend), are you root?"

        if cmd.startswith("sudo apt "):
            sub = cmd[9:].strip()
            if sub == "update":
                return "Hit:1 http://archive.ubuntu.com/ubuntu focal InRelease\nReading package lists... Done"
            if sub.startswith("install "):
                pkg = sub[8:].strip()
                return f"Reading package lists... Done\nBuilding dependency tree       \nReading state information... Done\n{pkg} is already the newest version (1.2.3-1)."
            return f"apt {sub}: command not found" # Realistic for some subcommands
        
        if cmd == "":
            return ""
        
        # FINAL FALLBACK: Local AI Generation (Crucial for complex pipes/commands)
        ai_response = _ask_ai(cmd, self.mode, self.cwd)
        if ai_response:
            return ai_response
            
        return f"-bash: {cmd.split()[0]}: command not found"

    def _windows_cmd(self, cmd: str) -> str:
        low = cmd.lower().strip()
        if low == "whoami":
            return "acme-dc01\\administrator"
        if low == "hostname":
            return "ACME-DC01"
        if low == "ipconfig":
            return """Windows IP Configuration

Ethernet adapter Ethernet0:
   Connection-specific DNS Suffix  . : acme.local
   IPv4 Address. . . . . . . . . . . : 10.0.1.10
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 10.0.1.1"""
        if low.startswith("dir"):
            path = "C:\\" if len(low) < 5 else cmd[4:].strip()
            contents = self.fs.get(path, self.fs.get("C:\\" + path.lstrip("\\"), []))
            if not contents:
                return "File Not Found"
            lines = [f" Volume in drive C has no label.", f" Volume Serial Number is 8C3F-2D19", f"", f" Directory of {path}", f""]
            for item in contents:
                is_dir = any(k.endswith(item) or k.endswith(item + "\\") for k in self.fs)
                dt = f"01/15/2024  {random.randint(1,12):02}:{random.randint(0,59):02} {'AM' if random.random() > 0.5 else 'PM'}"
                if is_dir:
                    lines.append(f"{dt}    <DIR>          {item}")
                else:
                    lines.append(f"{dt}         {random.randint(1000,999999):>9} {item}")
            lines.append(f"               {len(contents)} File(s)    {random.randint(10000, 999999):>10} bytes")
            return "\n".join(lines)
        if low == "systeminfo":
            return """Host Name:                 ACME-DC01
OS Name:                   Microsoft Windows Server 2019 Datacenter
OS Version:                10.0.17763 N/A Build 17763
System Type:               x64-based PC
Domain:                    acme.local"""
        if low in ("ver", "cmd"):
            return "Microsoft Windows [Version 10.0.17763.5458]"
        # Fall back to Ollama AI for unrecognized commands
        ai_response = _ask_ai(cmd, self.mode, self.cwd)
        if ai_response:
            return ai_response
        return f"'{cmd}' is not recognized as an internal or external command."

    def _iot_cmd(self, cmd: str) -> str:
        if cmd == "whoami":
            return "root"
        if cmd == "hostname":
            return "iot-sensor-GW-0042"
        if cmd == "uname -a":
            return "Linux iot-sensor-GW-0042 4.14.171 #1 SMP armv7l GNU/Linux"
        if cmd.startswith("cat /var/data/sensor_log.csv"):
            return """timestamp,sensor_id,temperature,humidity,pressure
2024-01-20T10:00:00Z,SENS-001,22.4,45.2,1013.25
2024-01-20T10:01:00Z,SENS-002,23.1,44.8,1013.20
2024-01-20T10:02:00Z,SENS-001,22.6,45.0,1013.22"""
        if cmd == "cat /etc/firmware.bin":
            return "[BINARY] IoT Gateway Firmware v2.3.1 — Build 20240115"
        if cmd.startswith("ls"):
            path = self.cwd
            parts = cmd.split()
            args = [p for p in parts[1:] if not p.startswith("-")]
            if args:
                path = args[0]
            return _ls_la(path, self.fs) if "-l" in cmd else "  ".join(self.fs.get(path, ["(empty)"]))
        if cmd == "pwd":
            return self.cwd
        # Fall back to Ollama AI for unrecognized commands
        ai_response = _ask_ai(cmd, self.mode, self.cwd)
        if ai_response:
            return ai_response
        return f"sh: {cmd.split()[0]}: not found"

    def calculate_command_risk(self, cmd: str) -> int:
        """Calculate a risk score (0-100) for a single command."""
        score = 0
        cmd = cmd.lower()
        
        # High-risk patterns
        critical = ["/etc/shadow", "id_rsa", "rm -rf", "mkfifo", "/dev/tcp", "python -c", "nc -e"]
        high = ["sudo", "nmap", "hydra", "wget", "curl", "chmod +x", "base64", "grep -r"]
        medium = ["cat ", "ls -la", "ping ", "find ", "ps aux"]

        if any(p in cmd for p in critical): score += 40
        elif any(p in cmd for p in high): score += 25
        elif any(p in cmd for p in medium): score += 10
        
        # Obfuscation detections
        if "base64" in cmd and "|" in cmd: score += 15
        if "${" in cmd: score += 10 # Variable expansion
        
        return min(40, score) # Max 40 per single command

    def get_profile(self) -> dict:
        """Return hacker profile analysis. Determinism-first logic with local AI refinement."""
        # 1. Base rule-based metrics
        skill = "Script Kiddie"
        if self.commands_run > 10: skill = "Intermediate"
        if self.commands_run > 20: skill = "Advanced"
        
        threat = min(100, self.commands_run * 3 + self.frustration)
        
        # 2. Local AI Assesment (Conserve resources, only every 10 cmds)
        if self.commands_run % 10 == 0:
            try:
                history_str = "\n".join([f"> {h['cmd']}" for h in self.history[-10:]])
                prompt = f"Analyze intent: {history_str}. Return JSON: {{'skill': str, 'threat': int}}"
                ai_data = shield_ai.generate(prompt, json_format=True)
                if isinstance(ai_data, dict):
                    skill = ai_data.get("skill", skill)
                    threat = ai_data.get("threat", threat)
            except:
                pass

        return {
            "threat_level": threat,
            "skill_level": skill,
            "frustration_index": self.frustration,
            "commands_executed": self.commands_run,
            "session_duration": round(time.time() - self.start_time, 1),
            "suspicious_commands": sum(1 for c in self.history if self.calculate_command_risk(c["cmd"]) > 15),
            "reverse_hack": self.reverse_hack_intel,
        }

    def get_attack_intel(self) -> dict:
        """Map all commands to MITRE ATT&CK techniques and kill chain phases."""
        triggered_techniques = []
        triggered_phases = set()
        phase_timeline = []

        for entry in self.history:
            cmd = entry["cmd"].lower()
            for patterns, tech_id, tech_name, phase in MITRE_ATTACK_MAP:
                if any(p in cmd for p in patterns):
                    technique = {
                        "technique_id": tech_id,
                        "technique_name": tech_name,
                        "phase": phase,
                        "command": entry["cmd"],
                        "timestamp": entry["time"],
                    }
                    # Avoid duplicate technique IDs for the same command
                    if not any(t["technique_id"] == tech_id and t["command"] == entry["cmd"]
                               for t in triggered_techniques):
                        triggered_techniques.append(technique)
                    triggered_phases.add(phase)
                    if phase not in [p["phase"] for p in phase_timeline]:
                        phase_timeline.append({"phase": phase, "timestamp": entry["time"]})

        # Build kill chain progress
        kill_chain = []
        for phase_info in KILL_CHAIN_PHASES:
            kill_chain.append({
                **phase_info,
                "active": phase_info["id"] in triggered_phases,
                "technique_count": sum(1 for t in triggered_techniques if t["phase"] == phase_info["id"]),
                "techniques": [t for t in triggered_techniques if t["phase"] == phase_info["id"]],
            })

        return {
            "kill_chain": kill_chain,
            "triggered_techniques": triggered_techniques,
            "active_phases": list(triggered_phases),
            "phase_timeline": phase_timeline,
            "total_techniques": len(triggered_techniques),
        }

    def predict_next_move(self) -> dict:
        """Predict attacker's next likely actions using Markov transitions + heuristics."""
        # Determine the current phase from recent commands
        current_phase = "recon"  # default
        for entry in reversed(self.history[-5:]):
            cmd = entry["cmd"].lower()
            for patterns, _, _, phase in MITRE_ATTACK_MAP:
                if any(p in cmd for p in patterns):
                    current_phase = phase
                    break
            else:
                continue
            break

        # Get base transition probabilities
        transitions = PHASE_TRANSITIONS.get(current_phase, PHASE_TRANSITIONS["recon"])

        # Build predictions with risk levels
        phase_names = {p["id"]: p["name"] for p in KILL_CHAIN_PHASES}
        risk_map = {
            "recon": "LOW",
            "initial_access": "MEDIUM",
            "execution": "HIGH",
            "persistence": "HIGH",
            "priv_esc": "CRITICAL",
            "credential_access": "HIGH",
            "collection": "CRITICAL",
        }

        # Boost probabilities based on command patterns seen so far
        predictions = []
        for next_phase, base_prob, description in transitions:
            # Adjust probability: if attacker hasn't explored this phase, increase likelihood
            intel = self.get_attack_intel()
            explored = intel["active_phases"]
            adj = base_prob
            if next_phase not in explored:
                adj = min(0.95, base_prob * 1.2)  # Slight boost for unexplored phases
            elif next_phase in explored and next_phase == "collection":
                adj = min(0.95, base_prob * 1.3)  # Collection often repeats

            predictions.append({
                "phase": next_phase,
                "phase_name": phase_names.get(next_phase, next_phase),
                "confidence": round(adj * 100),
                "risk_level": risk_map.get(next_phase, "MEDIUM"),
                "description": description,
                "countermeasure": self._get_countermeasure(next_phase),
            })

        # Sort by confidence desc and take top 3
        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        predictions = predictions[:3]

        return {
            "current_phase": current_phase,
            "current_phase_name": phase_names.get(current_phase, current_phase),
            "predictions": predictions,
            "commands_analyzed": len(self.history),
        }

    def _get_countermeasure(self, phase: str) -> str:
        """Return recommended countermeasure for a predicted phase."""
        countermeasures = {
            "recon": "Deploy additional decoy services to misdirect",
            "initial_access": "Rotate access credentials immediately",
            "execution": "Enable enhanced command logging and sandboxing",
            "persistence": "Monitor startup scripts and cron jobs",
            "priv_esc": "Lock down sudo access, deploy honey-tokens",
            "credential_access": "Rotate all exposed credentials, deploy canary tokens",
            "collection": "Isolate sensitive data stores, trigger containment",
        }
        return countermeasures.get(phase, "Monitor and log all activity")

    def generate_report(self, attacker_ip: str = "Unknown") -> dict:
        """Generate a comprehensive incident report."""
        intel = self.get_attack_intel()
        profile = self.get_profile()
        prediction = self.predict_next_move()
        duration = round(time.time() - self.start_time, 1)

        # Build timeline
        timeline = []
        for entry in self.history:
            risk = self.calculate_command_risk(entry["cmd"])
            techniques = []
            for patterns, tech_id, tech_name, phase in MITRE_ATTACK_MAP:
                if any(p in entry["cmd"].lower() for p in patterns):
                    techniques.append({"id": tech_id, "name": tech_name, "phase": phase})
            timeline.append({
                "command": entry["cmd"],
                "timestamp": entry["time"],
                "risk_score": risk,
                "techniques": techniques,
            })

        # Honey tokens accessed
        honey_keywords = ["aws_credentials", "prod.env", "deploy_keys", ".env", "shadow",
                          "id_rsa", "passwords", "employee_records"]
        tokens_accessed = sum(1 for c in self.history
                              if any(k in c["cmd"].lower() for k in honey_keywords))

        return {
            "report_id": f"IR-{int(time.time())}",
            "generated_at": time.time(),
            "session_duration": duration,
            "attacker_ip": attacker_ip,
            "threat_assessment": {
                "overall_risk": profile["threat_level"],
                "skill_level": profile["skill_level"],
                "frustration_index": profile["frustration_index"],
                "classification": "APT" if profile["threat_level"] > 80 else
                                  "Advanced" if profile["threat_level"] > 50 else
                                  "Opportunistic",
            },
            "mitre_attack": {
                "techniques_observed": len(intel["triggered_techniques"]),
                "phases_reached": len(intel["active_phases"]),
                "kill_chain": intel["kill_chain"],
                "techniques": intel["triggered_techniques"],
            },
            "session_stats": {
                "total_commands": self.commands_run,
                "suspicious_commands": profile["suspicious_commands"],
                "honey_tokens_accessed": tokens_accessed,
                "data_exfiltrated": "0 bytes (all decoy)",
            },
            "timeline": timeline,
            "recommendations": [
                "Rotate all credentials that were exposed in honeypot decoys",
                "Review firewall rules for the attacker's source IP",
                "Deploy additional monitoring on similar attack vectors",
                "Update IDS/IPS signatures based on observed TTPs",
                "Conduct threat hunt for similar activity across the network",
            ],
        }


class PDFReportHandler:
    def __init__(self):
        self.neon_green = HexColor("#00FF41")
        self.neon_cyan = HexColor("#00FFFF")
        self.neon_red = HexColor("#FF3131")
        self.cyber_bg = HexColor("#0A0E1A")
        self.grid_color = HexColor("#141E32")

    def _draw_background(self, c):
        c.setFillColor(self.cyber_bg)
        c.rect(0, 0, A4[0], A4[1], fill=1)

    def _draw_header(self, c, report_id):
        c.setStrokeColor(self.neon_green)
        c.setLineWidth(1)
        c.line(10*mm, A4[1] - 20*mm, A4[0] - 10*mm, A4[1] - 20*mm)
        
        c.setFont("Courier-Bold", 18)
        c.setFillColor(self.neon_green)
        c.drawString(12*mm, A4[1] - 15*mm, f">> LABYRINTH_FORGE // INCIDENT_REPORT // {report_id}")

    def generate(self, report: dict) -> bytes:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # --- PAGE 1: SYSTEM OVERVIEW ---
        self._draw_background(c)
        self._draw_header(c, report['report_id'])
        
        y = A4[1] - 35*mm
        
        c.setFont("Courier-Bold", 12)
        c.setFillColor(self.neon_cyan)
        c.drawString(15*mm, y, "[SYSTEM_STATUS]: OPERATIONAL")
        y -= 7*mm
        c.drawString(15*mm, y, f"[TIMESTAMP]: {datetime.fromtimestamp(report.get('generated_at', time.time())).strftime('%Y-%m-%d %H:%M:%S')}")
        y -= 7*mm
        c.drawString(15*mm, y, f"[SOURCE_IP]: {report['attacker_ip']}")
        y -= 7*mm
        c.drawString(15*mm, y, f"[SESSION_ID]: {report.get('session_id', 'LIVE_SESSION')}")
        
        y -= 15*mm
        
        # Threat Assessment Box
        c.setStrokeColor(self.neon_red)
        c.rect(12*mm, y - 55*mm, A4[0] - 24*mm, 60*mm)
        c.setFillColor(self.grid_color)
        c.rect(12*mm, y + 2*mm, 60*mm, 8*mm, fill=1)
        c.setFillColor(white)
        c.setFont("Courier-Bold", 10)
        c.drawString(15*mm, y + 4*mm, "THREAT_INTELLIGENCE")
        
        ta = report["threat_assessment"]
        stats = report["session_stats"]
        
        ty = y - 5*mm
        c.setFont("Courier", 10)
        c.setFillColor(white)
        items = [
            ("CLASSIFICATION", ta['classification']),
            ("RISK_SCORE", f"{ta['overall_risk']}%"),
            ("SKILL_LEVEL", ta['skill_level']),
            ("FRUSTRATION", f"{ta['frustration_index']}%"),
            ("CMD_EXECUTED", str(stats['total_commands'])),
            ("SUSP_ACTIVITY", str(stats['suspicious_commands'])),
            ("HONEY_TOKENS", str(stats['honey_tokens_accessed']))
        ]
        
        for label, val in items:
            c.setFillColor(self.neon_cyan)
            c.drawString(20*mm, ty, f"{label:15}:")
            c.setFillColor(white)
            c.drawString(60*mm, ty, val)
            ty -= 6*mm

        # MITRE ATTT&CK Summary
        y = ty - 15*mm
        c.setFillColor(self.grid_color)
        c.rect(12*mm, y + 2*mm, 60*mm, 8*mm, fill=1)
        c.setFillColor(white)
        c.setFont("Courier-Bold", 10)
        c.drawString(15*mm, y + 4*mm, "MITRE_ATT&CK_MATRIX")
        
        ma = report["mitre_attack"]
        ty = y - 5*mm
        c.setFont("Courier", 9)
        for tech in ma["techniques"][:10]:
            c.setFillColor(self.neon_red)
            c.drawString(15*mm, ty, f"[{tech['technique_id']}]")
            c.setFillColor(white)
            c.drawString(35*mm, ty, tech['technique_name'][:50])
            ty -= 5*mm
            if ty < 20*mm: break

        c.showPage()
        
        # --- PAGE 2: AI INSIGHTS & LOG STREAM ---
        self._draw_background(c)
        self._draw_header(c, report['report_id'])
        
        y = A4[1] - 35*mm
        c.setFillColor(self.grid_color)
        c.rect(12*mm, y + 2*mm, 60*mm, 8*mm, fill=1)
        c.setFillColor(self.neon_green)
        c.setFont("Courier-Bold", 10)
        c.drawString(15*mm, y + 4*mm, "AI_ANALYSIS_LOGS")
        
        ty = y - 8*mm
        c.setFont("Courier", 10)
        c.setFillColor(white)
        
        analysis = [
            f"[!] CORE_LOGIC: Behavioral pattern matches {ta['skill_level']} actor profile.",
            f"[!] NEURAL_NET: Intent assessed as {ta['classification']}.",
            f"[!] ANOMALY_ENGINE: {stats['suspicious_commands']} suspicious commands detected out of {stats['total_commands']}.",
            f"[!] EXFIL_CONTROL: {stats['honey_tokens_accessed']} honey-token interactions logged.",
            f"[!] FRUSTRATION_METRIC: {ta['frustration_index']}% deviation from expected actor SOP.",
            f"[!] KILL_CHAIN_PROGRESS: {report['mitre_attack']['phases_reached']}/7 phases identified.",
        ]
        
        for line in analysis:
            c.setFillColor(self.neon_green if "READY" in line else white)
            c.drawString(15*mm, ty, line)
            ty -= 6*mm
            
        ty -= 5*mm
        c.setFont("Courier-Bold", 10)
        c.setFillColor(self.neon_cyan)
        c.drawString(15*mm, ty, "COUNTERMEASURE_STATUS:")
        ty -= 6*mm
        c.setFont("Courier", 9)
        c.setFillColor(white)
        for rec in report.get("recommendations", []):
            c.drawString(15*mm, ty, f"[READY] {rec}")
            ty -= 5*mm

        # Log Stream
        y = ty - 15*mm
        c.setFillColor(self.grid_color)
        c.rect(12*mm, y + 2*mm, 60*mm, 8*mm, fill=1)
        c.setFillColor(white)
        c.setFont("Courier-Bold", 10)
        c.drawString(15*mm, y + 4*mm, "RAW_COMMAND_FEED")
        
        ty = y - 8*mm
        c.setFont("Courier", 8)
        for item in report["timeline"][-40:]: # Show more logs
            if ty < 20*mm:
                c.showPage()
                self._draw_background(c)
                self._draw_header(c, report['report_id'])
                ty = A4[1] - 35*mm
                
            dt = datetime.fromtimestamp(item["timestamp"]).strftime('%H:%M:%S')
            risk = "!" * (item["risk_score"] // 10) or "."
            
            c.setFillColor(self.neon_cyan)
            c.drawString(15*mm, ty, f"[{dt}]")
            c.setFillColor(self.neon_red if item["risk_score"] > 20 else white)
            c.drawString(35*mm, ty, f"[{risk:3}]")
            c.setFillColor(white)
            c.drawString(50*mm, ty, item["command"][:100])
            ty -= 4.5*mm

        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


# ── Demo simulation sequence ────────────────────────
DEMO_COMMANDS = [
    ("whoami", 1.2),
    ("pwd", 0.8),
    ("ls -la /", 1.5),
    ("cat /etc/passwd", 2.0),
    ("cd /home/sysadmin", 0.6),
    ("ls -la", 1.0),
    ("cd Documents", 0.5),
    ("ls -la", 1.2),
    ("cat aws_credentials.bak", 2.5),
    ("cat employee_records.csv", 2.0),
    ("cat deploy_keys.txt", 1.8),
    ("cd /var/www/html", 0.7),
    ("cat .env", 1.5),
    ("cd /home/deploy", 0.5),
    ("cat prod.env", 2.0),
    ("sudo su", 0.8),
    ("cat /etc/shadow", 1.0),
]

DAVE_MESSAGE = """
╔══════════════════════════════════════════════════╗
║  💬  Message from dave_it@acme-corp.internal     ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  Hey, are you fixing ticket #902?                ║
║  The DB migration script is failing again.       ║
║  Password for staging is: Stg_@dm1n_2024!       ║
║                                                  ║
║  - Dave from IT                                  ║
╚══════════════════════════════════════════════════╝
"""
