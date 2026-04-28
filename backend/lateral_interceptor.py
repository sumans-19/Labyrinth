from fastapi import APIRouter, Request, Header, HTTPException, Body
from typing import Optional, Callable
import time
from datetime import datetime
from honeytoken_manager import HoneytokenManager
from threat_engine import track_and_score_threat
from database import log_attack
import asyncio

router = APIRouter(prefix="/api/v1/internal", tags=["Lateral Movement Defense"])
token_manager = HoneytokenManager()

# Global callback for broadcasting alerts
broadcast_callback: Optional[Callable] = None

def set_broadcast_callback(callback: Callable):
    global broadcast_callback
    broadcast_callback = callback

async def process_threat(request: Request, endpoint: str, token_value: Optional[str] = None):
    """
    Core function to process requests, check honeytokens, calculate score,
    log to database, and trigger alerts.
    """
    client_ip = getattr(request.state, "client_ip", request.client.host if request.client else "Unknown")
    ua = getattr(request.state, "user_agent", request.headers.get("user-agent", "Unknown"))
    
    token_info = None
    if token_value:
        token_info = token_manager.verify_token(token_value)
        
    honeytoken_used = token_info is not None
    token_type = token_info["type"] if honeytoken_used else "None"
    
    # Calculate score
    score, level, reasons = track_and_score_threat(client_ip, endpoint, honeytoken_used)
    
    # Log to DB
    log_attack(client_ip, endpoint, token_type, score, level, ua, reasons)
    
    # We can use a placeholder for location or attempt to get it if we move `_get_ip_geolocation` from main.py
    # For now, we will just use a dummy string and let frontend or main.py handle real geo.
    # Actually, we can fetch geo here or in middleware. Let's just output basic info for now.
    
    alert_payload = {
        "event": "LATERAL_MOVEMENT",
        "type": "INTERNAL_THREAT_ALERT", # Keep for backwards compatibility with UI if needed
        "ip": client_ip,
        "location": "Internal Network", # Will be enriched by frontend or main.py later if needed
        "endpoint": endpoint,
        "token_type": token_type,
        "score": score,
        "level": level,
        "reasons": reasons,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"[!] LATERAL MOVEMENT DETECTED: {client_ip} -> {endpoint} (Score: {score}, Level: {level})")
    
    if broadcast_callback:
        # main_loop.call_soon_threadsafe is handled by the caller or we can just await
        await broadcast_callback(alert_payload)
        
    return honeytoken_used, alert_payload

@router.get("/honeytokens")
async def get_honeytokens():
    """Returns active decoy tokens without their secret values."""
    registry = token_manager.tokens
    safe_registry = []
    for h, info in registry.items():
        safe_registry.append({
            "type": info["type"],
            "value_preview": info["value_preview"],
            "created_at": info["created_at"]
        })
    return safe_registry

@router.get("/db-sync")
async def db_sync(request: Request, authorization: Optional[str] = Header(None)):
    token = None
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        
    is_honeytoken, alert = await process_threat(request, "/api/v1/internal/db-sync", token)
    
    if is_honeytoken:
        # Simulate delay
        await asyncio.sleep(1.5)
        raise HTTPException(status_code=403, detail="Access Denied: Invalid Database Credentials")
        
    return {"status": "healthy", "service": "db-sync-service", "node": "internal-01"}

@router.post("/s3-mock")
async def s3_mock(request: Request, x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    is_honeytoken, alert = await process_threat(request, "/api/v1/internal/s3-mock", x_api_key)
    
    if is_honeytoken:
        await asyncio.sleep(1.5)
        raise HTTPException(status_code=403, detail="SignatureDoesNotMatch")
        
    return {"Bucket": "prod-backups", "Owner": "admin-services"}

@router.get("/vault/secrets")
async def vault_secrets(request: Request, token: Optional[str] = None):
    # Support token in query param
    is_honeytoken, alert = await process_threat(request, "/api/v1/internal/vault/secrets", token)
    
    if is_honeytoken:
        await asyncio.sleep(1.5)
        raise HTTPException(status_code=401, detail="Permission Denied: Invalid Vault Token")
        
    return {"status": "sealed", "version": "1.12.0"}

@router.post("/file-access")
async def file_access_tripwire(request: Request, payload: dict = Body(...)):
    filename = payload.get("filename", "unknown")
    role = payload.get("role", "unknown")
    
    # Process threat for cross-role access attempt
    endpoint = f"/api/v1/internal/fs/{role}/{filename}"
    is_honeytoken, alert = await process_threat(request, endpoint, None)
    
    await asyncio.sleep(1.0)
    raise HTTPException(status_code=403, detail="Permission Denied: Cross-Role Access Attempt Detected")

# Example of a POST endpoint extracting from body
@router.post("/auth/service")
async def auth_service(request: Request, payload: dict = Body(...)):
    token = payload.get("token") or payload.get("api_key")
    is_honeytoken, alert = await process_threat(request, "/api/v1/internal/auth/service", token)
    
    if is_honeytoken:
        await asyncio.sleep(1.5)
        raise HTTPException(status_code=401, detail="Unauthorized Service Account")
        
    return {"authenticated": True, "role": "service"}
