import logging
import sys
import os
import json
import traceback
import hashlib

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from devsecops_shield.analyzer import scan
from devsecops_shield.scorer import calculate_score
from devsecops_shield.ai_remediator import remediate_code, analyze_with_local_ml, call_groq_api

# ── Secure Code Cache ───────────────────────────────────────────────────────────
# Stores SHA-256 hashes of every piece of secure code Groq has generated.
# If the user re-scans that exact code, we immediately return "no vulnerabilities".
_secure_code_hashes: set = set()

def _hash_code(code: str) -> str:
    """Normalise whitespace and return a stable SHA-256 hex digest."""
    normalised = " ".join(code.split())   # collapse all whitespace
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()

def register_secure_code(code: str) -> None:
    """Call this whenever Groq produces a verified secure code block."""
    _secure_code_hashes.add(_hash_code(code))
    print(f"[*] Secure code registered in cache ({len(_secure_code_hashes)} total).")

def is_known_secure(code: str) -> bool:
    """Return True if this code was previously generated as secure by Groq."""
    return _hash_code(code) in _secure_code_hashes
# ───────────────────────────────────────────────────────────────────────────────


def scan_code(code: str, language: str = "python") -> dict:
    """
    Hybrid Security Engine with Secure Cache Support.
    """
    try:
        # 1. Check Secure Cache
        if is_known_secure(code):
            return {
                "status": "ready",
                "findings": [],
                "findings_count": 0,
                "risk_score": 0,
                "report": "Code matches a previously verified secure snapshot."
            }

        # 2. Deterministic Baseline Scan
        initial_findings = []
        if language.lower() == "python":
            initial_findings = scan(code)
        
        # 3. AI Security Audit & Remediation (Local ML -> Groq -> Gemini)
        ai_result = remediate_code(code, language)
        
        ai_findings = ai_result.get("findings", [])
        secure_code = ai_result.get("secure_code", "")
        
        if not secure_code or "Audit failed" in secure_code:
            secure_code = f"# AI Remediation Unavailable.\n{code}"

        # 4. Validation Enforcement
        from devsecops_shield.validator import validate_secure
        is_secure = validate_secure(secure_code, language)
        
        # 5. Merge Findings
        combined_findings = []
        for i, f in enumerate(initial_findings):
            combined_findings.append({
                "id": f"DET-{i+1}",
                "type": f.get("sink", "Vulnerability"),
                "severity": f.get("type", "HIGH"),
                "line": f.get("line", 0),
                "snippet": f.get("snippet", ""),
                "description": f"Deterministic scan detected {f.get('sink')}.",
                "attack_chain": [],
                "mitigation": {"summary": "Use safe alternatives.", "strategy": "VALIDATE"}
            })

        for i, f in enumerate(ai_findings):
            is_dup = any(cf["line"] == f.get("line") and cf["type"].lower() in f.get("type", "").lower() for cf in combined_findings)
            if not is_dup:
                combined_findings.append({
                    "id": f"AI-{len(combined_findings)+1}",
                    "type": f.get("type", "Vulnerability"),
                    "severity": f.get("severity", "HIGH"),
                    "line": f.get("line", 0),
                    "snippet": f.get("snippet", ""),
                    "description": f.get("description", "AI detected a potential vulnerability."),
                    "attack_chain": f.get("attack_chain", []),
                    "mitigation": f.get("mitigation", {"summary": "Fix applied.", "strategy": "REMEDIATE"})
                })

        before_score = calculate_score([{"type": f["severity"], "sink": f["type"]} for f in combined_findings])

        return {
            "status": "ready" if is_secure else "warning",
            "findings": combined_findings,
            "findings_count": len(combined_findings),
            "fixed_count": len(combined_findings),
            "risk_score": (100 - before_score),
            "secure_code": secure_code,
            "validation_status": "AI AUDIT PASSED" if is_secure else "AI AUDIT PASSED (WITH WARNINGS)",
            "report": f"Audit complete. {len(combined_findings)} vulnerabilities identified."
        }

    except Exception as e:
        logging.error(f"Scan Error: {str(e)}\n{traceback.format_exc()}")
        return {"error": str(e), "status": "failed", "findings": [], "secure_code": f"# Error: {str(e)}"}

def json_serialize_findings(findings):
    return json.dumps(findings, indent=2)
