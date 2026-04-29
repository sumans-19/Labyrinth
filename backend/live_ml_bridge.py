import asyncio
import time
from ml_ensemble import ensemble as ml_ensemble_instance
from honeypot import shield_ai, HoneypotSession

def derive_ensemble_features(session: HoneypotSession) -> dict:
    """Extract behavioral features from a live honeypot session for the Neural Ensemble."""
    history = session.history
    cmds = [h["cmd"] for h in history]
    times = [h["time"] for h in history]
    n = len(cmds)
    
    # Calculate avg delay
    delays = [times[i] - times[i-1] for i in range(1, len(times))] if n > 1 else [3.0]
    avg_delay_s = sum(delays) / len(delays) if delays else 3.0
    
    # Duration and typing speed
    duration = times[-1] - times[0] if n > 1 else 1.0
    total_chars = sum(len(c) for c in cmds)
    typing_speed = (total_chars / max(duration, 1)) * 60 / 5 # WPM approx
    
    # Diversity
    unique = len(set(cmds))
    diversity = unique / max(n, 1)
    
    # Dangerous keywords
    dangerous_keywords = ["sudo", "shadow", "id_rsa", "wget", "curl", "nc ", "nmap", "hydra",
                          "chmod", "base64", "rm -rf", "python -c", "bash -c"]
    danger_count = sum(1 for c in cmds if any(k in c.lower() for k in dangerous_keywords))
    danger_ratio = danger_count / max(n, 1)
    
    # Error rate (simulated or derived from density)
    error_rate = min(30, (danger_ratio * 40) + (n * 0.5))
    
    return {
        "avg_keystroke_delay_ms": avg_delay_s * 1000,
        "typing_speed_wpm": typing_speed,
        "error_rate_pct": error_rate,
        "command_diversity": diversity,
        "session_duration_s": duration,
        "unique_commands": float(unique),
        "dangerous_cmd_ratio": danger_ratio,
        "time_between_commands_ms": avg_delay_s * 1000,
        "backspace_frequency": 0.08 + (danger_ratio * 0.15),
        "paste_frequency": 0.1 + (0.3 if avg_delay_s < 0.5 else 0),
    }

async def run_ensemble_analysis(session: HoneypotSession) -> tuple:
    """Run the 3-model ensemble + AI narration on a live session."""
    ensemble_result = None
    ai_narration = None
    try:
        features = derive_ensemble_features(session)
        # Use to_thread for blocking ML calls
        ensemble_result = await asyncio.to_thread(ml_ensemble_instance.predict, features)
        
        if ensemble_result and "error" not in ensemble_result:
            prompt = (
                f"LIVE THREAT ANALYSIS — Neural Ensemble Report\n"
                f"Threat Score: {ensemble_result['ensemble_threat_score']}/100\n"
                f"Frustration Index: {ensemble_result['frustration_index']}/100\n"
                f"Anomalous: {'YES' if ensemble_result['isolation_forest']['is_anomaly'] else 'NO'}\n"
                f"Classification: {'Malicious' if ensemble_result['xgboost']['prediction'] == 1 else 'Benign'}\n"
                f"Malicious Prob: {ensemble_result['xgboost']['malicious_prob']}%\n"
                f"Tarpit Strategy: {ensemble_result['tarpit_strategy']}\n"
                f"Commands: {session.commands_run} | Duration: {round(time.time() - session.start_time)}s\n\n"
                f"In 2 sentences, narrate the adaptive defense strategy and "
                f"the psychological goal of the Labyrinth right now."
            )
            try:
                response = await asyncio.to_thread(shield_ai.generate_content, prompt)
                if response and hasattr(response, 'text') and response.text:
                    ai_narration = response.text.strip()
            except Exception:
                ai_narration = f"Tarpit {ensemble_result['tarpit_strategy']} active. Threat score {ensemble_result['ensemble_threat_score']}/100."
    except Exception as e:
        print(f"[!] Ensemble Analysis Error: {e}")
        
    return ensemble_result, ai_narration

def build_command_telemetry(session, command, output, profile, attack_intel, prediction):
    """Helper to structure command analysis for the dashboard."""
    risk_score = session.calculate_command_risk(command)
    
    # Map risk to levels
    risk_level = "LOW"
    if risk_score > 70: risk_level = "CRITICAL"
    elif risk_score > 40: risk_level = "HIGH"
    elif risk_score > 20: risk_level = "MEDIUM"

    # Find matched techniques for this specific command
    matched_techniques = [t for t in attack_intel.get("triggered_techniques", []) if t["command"] == command]

    return {
        "command": command,
        "output_preview": (output[:200] + "...") if len(output) > 200 else output,
        "output_lines": len(output.split("\n")),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "matched_techniques": matched_techniques,
        "current_phase": prediction.get("current_phase_name", "Reconnaissance"),
        "timestamp": time.time() * 1000
    }
