import logging
import sys
import os
import json

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from devsecops_shield.analyzer import scan
from devsecops_shield.scorer import calculate_score
from devsecops_shield.ai_remediator import remediate_code
from devsecops_shield.validator import validate_secure

def scan_code(code: str, language: str = "python") -> dict:
    """
    Super-Intelligence Bridge: Leading with AI Analysis & Remediation.
    """
    try:
        # 1. AI Security Audit & Remediation (One-Pass Deep Reasoning)
        ai_result = remediate_code(code, language)
        
        ai_findings = ai_result.get("findings", [])
        secure_code = ai_result.get("secure_code", "# AI Error: No code returned.")

        # 2. Validation Enforcement (Silent Deterministic Gate)
        is_secure = validate_secure(secure_code, language)
        
        # 3. Post-Fix Verification Scan
        # We still run a deterministic scan on the AI's output for final scoring if Python
        if language.lower() == "python":
            from devsecops_shield.analyzer import scan as final_verify_scan
            after_findings = final_verify_scan(secure_code)
            after_score = calculate_score(after_findings)
            before_score = calculate_score([{"type": f["severity"], "sink": f["type"]} for f in ai_findings])
        else:
            after_score = 100 if is_secure else 0
            before_score = calculate_score([{"type": f["severity"], "sink": f["type"]} for f in ai_findings])

        # 5. Format Findings for UI (Using AI's Deep Analysis)
        formatted_findings = []
        for i, f in enumerate(ai_findings):
            formatted_findings.append({
                "id": f"AI-AUDIT-{i+1}",
                "type": f.get("type", "Vulnerability"),
                "severity": f.get("severity", "HIGH"),
                "line": f.get("line", 0),
                "snippet": f.get("snippet", "Context provided by AI"),
                "description": f.get("description", "Structural flaw identified by deep analysis."),
                "attack_chain": f.get("attack_chain", []),
                "mitigation": f.get("mitigation", {"summary": "Fix applied.", "patched_snippet": "", "strategy": "VALIDATE"})
            })

        return {
            "status": "ready" if is_secure else "failed",
            "findings": formatted_findings,
            "findings_count": len(ai_findings),
            "fixed_count": len(ai_findings) if is_secure else 0,
            "risk_score": (100 - before_score), # ALWAYS use before_score for initial risk
            "secure_code": secure_code if is_secure else "# SECURITY VETO: AI remediation failed structural safety enforcement.",
            "validation_status": "AI COGNITIVE AUDIT PASSED" if is_secure else "AI VETO TRIPPED",
            "report": f"AI Cognitive Audit complete. {len(ai_findings)} structural flaws identified and neutralized by shield-engine oracle. Verification: {'SUCCESS' if is_secure else 'CRITICAL FAILURE'}."
        }

    except Exception as e:
        import traceback
        logging.error(f"AI intelligence Error: {str(e)}\n{traceback.format_exc()}")
        return {"error": str(e), "status": "failed"}

    except Exception as e:
        import traceback
        logging.error(f"Modular Shield Error: {str(e)}\n{traceback.format_exc()}")
        return {"error": str(e), "status": "failed"}

def json_serialize_findings(findings):
    import json
    return json.dumps(findings, indent=2)
