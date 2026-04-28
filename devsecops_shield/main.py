import os
import sys
from devsecops_shield.analyzer import scan
from devsecops_shield.scorer import calculate_score
from devsecops_shield.ai_remediator import remediate_code
from devsecops_shield.validator import validate_secure

def run_shield(file_path):
    """
    Super-Intelligence Execution Engine: Orchestrates AI Audit & Remediation.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File {file_path} not found.")
        return

    with open(file_path, "r", encoding='utf-8') as f:
        source = f.read()

    print("\n" + "="*50)
    print("🛡️  INITIALIZING DEVSECOPS SHIELD v3.0 (AI-FIRST)")
    print("="*50)

    print("\n🤖 STEP 1: Executing AI Security Audit & Remediation...")
    ai_result = remediate_code(source)
    
    findings = ai_result.get("findings", [])
    secure_code = ai_result.get("secure_code", "# AI Error")
    threat_analysis = ai_result.get("threat_analysis", "")

    print(f"📊 AI Detected {len(findings)} Vulnerabilities.")
    for f in findings:
        print(f"  [!] {f.get('type')} (Line {f.get('line')}): {f.get('description')}")
        
    if threat_analysis:
        analysis_file = "threat_analysis.md"
        with open(analysis_file, "w", encoding='utf-8') as f:
            f.write(threat_analysis)
        print(f"\n📖 Educational Threat Analysis generated -> {analysis_file}")

    # ALWAYS write to debug file for analysis
    with open("debug_output.py", "w", encoding='utf-8') as f:
        f.write(secure_code)

    print("\n🔎 STEP 2: Structural Validation Gatekeeping...")
    if not validate_secure(secure_code):
        print("❌ CRITICAL VETO: AI remediation failed structural safety enforcement.")
        return

    # Post-fix scoring
    from devsecops_shield.analyzer import scan as final_verify_scan
    after_issues = final_verify_scan(secure_code)
    after_score = calculate_score(after_issues)

    print(f"📈 Integrity Verification PASSED. Final Score: {after_score}/100")

    output_file = "secure_output.py"
    with open(output_file, "w", encoding='utf-8') as f:
        f.write(secure_code)

    print(f"\n✅ SUCCESS: Autonomous Security Hardening complete -> {output_file}")
    print("="*50 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_shield(sys.argv[1])
    else:
        # Default to a test file if exists
        test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "ad_vulnerable.py")
        if os.path.exists(test_file):
            run_shield(test_file)
        else:
            print("Usage: python -m devsecops_shield.main <vulnerable_file.py>")
