import paramiko
import time
import sys

def test_ssh_connection(host="127.0.0.1", port=2222, user="sysadmin"):
    print(f"[*] Attempting connection to {host}:{port} as {user}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=user, password="password", timeout=5)
        
        print("[+] Connection successful!")
        shell = client.invoke_shell()
        time.sleep(1)
        
        # Send a command
        shell.send("ls -la\n")
        time.sleep(1)
        output = shell.recv(65535).decode("utf-8")
        print("[+] Received output:")
        print(output)
        
        if "total" in output.lower():
            print("[SUCCESS] Command mirrored and output received.")
        else:
            print("[FAILURE] Unexpected output.")
            
        shell.close()
        client.close()
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_ssh_connection()
