import sys
import os

# Mock GroqClient
class MockGroq:
    def generate(self, prompt, json_format=False):
        if "sudo" in prompt.lower():
            return "[AI] Executing as root: Success."
        return "[AI] Standard command output."

# Mock shielding
import sys
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import HoneypotSession after setting up mocks or ensuring environment
try:
    from backend.honeypot import HoneypotSession
    session = HoneypotSession()
    
    # Test sudo
    print("Testing sudo...")
    output = session.process_command("sudo tail -n 5 /var/log/auth.log")
    print(f"Output: {output}")
    
    # Test nano
    print("\nTesting nano...")
    output = session.process_command("nano config.yaml")
    print(f"Output: {output[:100]}...") # Print first 100 chars
    
    # Test gedit
    print("\nTesting gedit...")
    output = session.process_command("gedit main.py")
    print(f"Output: {output}")
    
    # Test complex find
    print("\nTesting complex find...")
    output = session.process_command("find /etc -type f -name \"*.conf\" 2>/dev/null | xargs grep -l \"auth\"")
    print(f"Output: {output}")

except ImportError as e:
    print(f"Import Error: {e}")
except Exception as e:
    print(f"Error: {e}")
