from fastapi import APIRouter, Request, Header, HTTPException, Depends
from typing import Optional, Callable
import time
from honeytoken_manager import HoneytokenManager

router = APIRouter(prefix="/api/v1/internal", tags=["Lateral Movement Defense"])
token_manager = HoneytokenManager()

# Global callback for broadcasting alerts
broadcast_callback: Optional[Callable] = None

def set_broadcast_callback(callback: Callable):
    global broadcast_callback
    broadcast_callback = callback

async def trigger_lateral_alert(request: Request, token_info: dict, used_token: str, endpoint: str):
    client_ip = request.client.host if request.client else "Unknown"
    # Check for X-Forwarded-For if behind a proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        
    ua = request.headers.get("user-agent", "Unknown")
    timestamp = time.time() * 1000 # JS compatible timestamp
    
    # Forensic Intel Structure matching main.py's expected UI format
    source_info = {
        "ip": client_ip,
        "ua": ua,
        "hostname": f"PROBE-{client_ip.replace('.', '-')}",
        "network": "LATERAL_MOVEMENT_NODE",
        "location": "Internal Infrastructure",
        "os": "Detected via Agent",
        "browser": "N/A (API Probe)",
        "device_type": "SERVER/ROUTER",
        "isp": "Internal LAN",
        "org": "Corporate Intranet",
        "access_time": datetime.now().isoformat()
    }

    alert_payload = {
        "type": "INTERNAL_THREAT_ALERT", # Reusing type for UI compatibility
        "alert_category": "LATERAL_MOVEMENT",
        "severity": "CRITICAL",
        "timestamp": timestamp,
        "document_name": f"Honeytoken: {token_info['type']}",
        "ip_address": client_ip,
        "user_agent": ua,
        "source_info": source_info,
        "token_used": used_token[:12] + "...",
        "target_endpoint": endpoint,
        "is_authorized": False,
        "details": f"Lateral movement detected! Attacker used fake {token_info['type']} from registered honeytokens to access {endpoint}."
    }
    
    print(f"[!] LATERAL MOVEMENT DETECTED from {client_ip} on {endpoint}")
    
    if broadcast_callback:
        await broadcast_callback(alert_payload)
    return alert_payload

@router.get("/db-sync")
async def db_sync(request: Request, authorization: Optional[str] = Header(None)):
    if authorization:
        # Expecting "Bearer <token>" or just "<token>"
        token = authorization.replace("Bearer ", "").strip()
        token_info = token_manager.verify_token(token)
        if token_info:
            await trigger_lateral_alert(request, token_info, token, "/api/v1/internal/db-sync")
            raise HTTPException(status_code=403, detail="Access Denied")
            
    return {"status": "healthy", "service": "db-sync-service", "node": "internal-01"}

@router.post("/s3-mock")
async def s3_mock(request: Request, x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    if x_api_key:
        token_info = token_manager.verify_token(x_api_key)
        if token_info:
            await trigger_lateral_alert(request, token_info, x_api_key, "/api/v1/internal/s3-mock")
            raise HTTPException(status_code=403, detail="SignatureDoesNotMatch")
            
    return {"Bucket": "prod-backups", "Owner": "admin-services"}

@router.get("/vault/secrets")
async def vault_secrets(request: Request, token: Optional[str] = None):
    # Support token in query param for some internal scripts
    if token:
        token_info = token_manager.verify_token(token)
        if token_info:
            await trigger_lateral_alert(request, token_info, token, "/api/v1/internal/vault/secrets")
            raise HTTPException(status_code=401, detail="Permission Denied")
            
    return {"status": "sealed", "version": "1.12.0"}
