import asyncio
import json
import os
import sys

# Try to import websockets, suggest install if missing
try:
    import websockets
except ImportError:
    print("Error: 'websockets' library not found.")
    print("Please run: pip install websockets")
    sys.exit(1)

async def attacker_cli():
    # Allow passing host IP as argument
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    uri = f"ws://{host}:8000/ws/attacker"
    print("\x1b[1;36m╔══════════════════════════════════════╗\x1b[0m")
    print("\x1b[1;36m║     LABYRINTH FORGE — ATTACKER CLI   ║\x1b[0m")
    print("\x1b[1;36m╚══════════════════════════════════════╝\x1b[0m")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("\x1b[1;32m[CONNECTED]\x1b[0m Tunnel established to War Room dashboard.\n")
            
            # Receive init message
            init_data = await websocket.recv()
            init_msg = json.loads(init_data)
            prompt = init_msg.get("prompt", "$ ")
            
            while True:
                try:
                    # Get command from user
                    cmd = input(f"\x1b[1;32m{prompt}\x1b[0m")
                    if cmd.lower() in ["exit", "quit"]:
                        break
                    
                    # Send command to server
                    await websocket.send(json.dumps({
                        "type": "command",
                        "command": cmd
                    }))
                    
                    # Receive response
                    resp_data = await websocket.recv()
                    resp_msg = json.loads(resp_data)
                    
                    if resp_msg.get("output"):
                        print(resp_msg["output"])
                    
                    prompt = resp_msg.get("prompt", prompt)
                    
                except EOFError:
                    break
                except Exception as e:
                    print(f"\x1b[1;31m[ERROR]\x1b[0m {e}")
                    break
    except Exception as e:
        print(f"\x1b[1;31m[CONNECTION ERROR]\x1b[0m Could not connect to {uri}")
        print("Make sure the Labyrinth Forge backend is running.")

if __name__ == "__main__":
    try:
        asyncio.run(attacker_cli())
    except KeyboardInterrupt:
        print("\n\x1b[1;33m[DISCONNECTED]\x1b[0m Session closed by user.")
