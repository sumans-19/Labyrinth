from devsecops_shield.analyzer import scan

def validate_secure(code, language="python"):
    """
    Enforcement engine: Re-scans the AI output.
    Returns False if ANY Critical issues persist or if code is invalid.
    """
    if not code or code.startswith("# ERROR") or code.startswith("// ERROR"):
        return False

    if language.lower() != "python":
        # We only support deterministic AST validation for Python right now
        # We rely solely on the AI Oracle for non-Python languages
        return True

    issues = scan(code)
    for issue in issues:
        # Strict enforcement: Any CRITICAL or PARSE_ERROR is a failure
        if issue["type"] in ["CRITICAL", "PARSE_ERROR"]:
            return False
    return True
