from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from threat_engine import is_ip_blacklisted
import time
import asyncio

logger = logging.getLogger("labyrinth")
logger.setLevel(logging.INFO)

class GlobalMonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract IP robustly
        client_ip = request.client.host if request.client else "Unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
            
        ua = request.headers.get("user-agent", "Unknown")
        endpoint = request.url.path
        
        # Check blacklist
        if is_ip_blacklisted(client_ip):
            logger.warning(f"BLOCKED REQUEST from {client_ip} to {endpoint}")
            # Add delay to simulate tarpitting (async delay)
            await asyncio.sleep(2)
            return JSONResponse(
                status_code=403, 
                content={"error": "Access Denied", "detail": "Your IP has been flagged for malicious activity."}
            )
            
        # Attach metadata to request state
        request.state.client_ip = client_ip
        request.state.user_agent = ua
        
        # We don't log every single request to console in production, but for prototype it's fine.
        if endpoint.startswith("/api/v1/internal"):
            logger.info(f"Internal endpoint accessed: {client_ip} - {endpoint} - {ua}")
        
        response = await call_next(request)
        return response
