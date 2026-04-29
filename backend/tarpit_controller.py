import time
import json
import asyncio
from typing import Dict, Any

class TarpitController:
    """
    Handles the Tarpit mechanism (artificial latency) and alerts the WebSocket manager.
    """
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.is_active = False
        self.delay_seconds = 2.0  # Default delay to slow down attackers

    def activate_tarpit(self, profile_id: str, confidence: float):
        """Activates the tarpit status and prepares alerts."""
        self.is_active = True
        print(f"[!] TARPIT ACTIVATED: Returning Attacker Detected ({profile_id}) with {confidence:.2%} confidence.")
        
        # Format event payload for React dashboard
        payload = {
            "event": "TARPIT_TRIGGERED",
            "data": {
                "profile_id": profile_id,
                "confidence_score": round(confidence, 4),
                "status": "Tarpit Activated",
                "latency_applied": f"{self.delay_seconds}s",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        # In a real async environment, we'd send this to the websocket
        self._send_to_dashboard(payload)

    def apply_latency(self):
        """Introduces artificial delay if the tarpit is active."""
        if self.is_active:
            # We use a slight random variance to make it feel like "lag" rather than a fixed block
            jitter = self.delay_seconds + (0.1 * (time.time() % 5))
            time.sleep(jitter)

    def _send_to_dashboard(self, payload: Dict[str, Any]):
        """Simulates sending payload to WebSocket manager."""
        print(f"[DEBUG] WebSocket Payload Sent: {json.dumps(payload, indent=2)}")
        # Integration logic with actual WebSocket manager goes here
        # Example: await self.websocket_manager.broadcast(payload)
        pass

    def reset(self):
        """Resets the tarpit state."""
        self.is_active = False
