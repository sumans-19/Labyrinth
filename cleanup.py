import os
import subprocess
import socket

def kill_process_on_port(port):
    print(f"[*] Checking for processes on port {port}...")
    try:
        output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        for line in output.strip().split('\n'):
            parts = line.split()
            if len(parts) > 4:
                pid = parts[-1]
                print(f"[*] Killing process {pid} on port {port}...")
                subprocess.run(f"taskkill /F /PID {pid}", shell=True)
    except subprocess.CalledProcessError:
        print(f"[+] Port {port} is clear.")

def check_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    print("═══ LABYRINTH FORGE CLEANUP & DIAGNOSTIC ═══\n")
    
    # 1. Kill zombie processes
    kill_process_on_port(8000)
    kill_process_on_port(3000)
    kill_process_on_port(2222)
    
    # 2. Verify IP
    ip = check_local_ip()
    print(f"\n[!] YOUR CURRENT HOST IP: {ip}")
    print(f"[!] DO NOT USE 'localhost' ON YOUR FRIEND'S LAPTOP.")
    print(f"[!] USE '{ip}' INSTEAD.\n")
    
    # 3. Final Warning
    print("═══ READY TO RESTART ═══")
    print("1. Start Backend: python -m uvicorn main:app --host 0.0.0.0 --port 8000")
    print("2. Start Frontend: npm run dev")
    print("3. Ensure your friend is on the SAME Wi-Fi as you.")
