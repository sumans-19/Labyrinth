import os
from dotenv import load_dotenv

# Load environment from root or backend if needed
def load_env_robustly():
    # 1. Check current directory
    load_dotenv(override=True)
    
    # 2. Check project root (assuming we are 1 level deep)
    root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(root_env):
        load_dotenv(root_env, override=True)
    
    # 3. Check 'backend' directory explicitly
    backend_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', '.env')
    if os.path.exists(backend_env):
        load_dotenv(backend_env, override=True)

load_env_robustly()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GROQ_API_KEY and not GEMINI_API_KEY:
    # Print debug info instead of just crashing instantly to help diagnostics
    print(f"CRITICAL: No AI keys found in environment!")
    print(f"Current Working Directory: {os.getcwd()}")
    # We still raise it because the application requires it for AI features
    raise RuntimeError("AI keys (GROQ or GEMINI) not set in environment. Please check your backend/.env file.")

MODEL = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-1.5-flash"
