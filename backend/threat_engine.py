from typing import Dict, List, Tuple
from datetime import datetime, timedelta

# In-memory store to track request timestamps per IP for repeated attempt logic
_ip_request_history: Dict[str, List[datetime]] = {}

def track_and_score_threat(ip: str, endpoint: str, honeytoken_used: bool) -> Tuple[int, str, List[str]]:
    """
    Calculates the threat score and level for a given access attempt.
    
    Rules:
    - Honeytoken used -> +40
    - Internal endpoint accessed -> +30
    - Repeated attempts -> +20
    """
    now = datetime.now()
    if ip not in _ip_request_history:
        _ip_request_history[ip] = []
        
    # Clean up old history (older than 10 minutes)
    _ip_request_history[ip] = [t for t in _ip_request_history[ip] if now - t < timedelta(minutes=10)]
    
    # We don't append here immediately, we let the interceptor/middleware decide when to call this.
    # Actually, if we call this function, we consider it an attempt.
    _ip_request_history[ip].append(now)
    
    score = 0
    reasons = []
    
    if honeytoken_used:
        score += 40
        reasons.append("Honeytoken used")
        
    # Check if internal endpoint
    if endpoint.startswith("/api/v1/internal") or "/internal/" in endpoint:
        score += 30
        reasons.append("Internal endpoint accessed")
        
    # Check for repeated attempts (e.g., more than 2 in 10 minutes)
    if len(_ip_request_history[ip]) > 2:
        score += 20
        reasons.append("Repeated attempts")
        
    # Determine level
    if score >= 90:
        level = "CRITICAL"
    elif score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"
        
    return score, level, reasons

def is_ip_blacklisted(ip: str) -> bool:
    """Check if an IP is blacklisted due to too many rapid attempts."""
    if ip in _ip_request_history:
        # For simulation, more than 5 attempts in 10 minutes = blacklisted
        if len(_ip_request_history[ip]) > 5:
            return True
    return False
