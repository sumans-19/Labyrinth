import re
from typing import List, Dict, Any

class BehaviorExtractor:
    """
    Extracts behavioral features from raw terminal commands and timestamps.
    """
    def __init__(self):
        # List of common commands that might be typos or errors
        self.error_indicators = ["command not found", "syntax error", "permission denied"]

    def extract_features(self, session_commands: List[str], timestamps: List[float]) -> Dict[str, Any]:
        """
        Processes a session to extract N-grams, typing speed, and error rate.
        """
        if not session_commands:
            return {
                "raw_sequence": "",
                "ngrams": [],
                "avg_delay": 0.0,
                "error_rate": 0.0
            }

        # 1. Raw Command Sequence
        raw_sequence = " ".join(session_commands)

        # 2. Command N-Grams
        ngrams = self._generate_ngrams(session_commands, [2, 3])

        # 3. Typing Speed / Delay (in seconds)
        avg_delay = 0.0
        if len(timestamps) > 1:
            delays = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            # Filter out extreme delays (e.g., hacker went for coffee)
            filtered_delays = [d for d in delays if d < 60]
            if filtered_delays:
                avg_delay = sum(filtered_delays) / len(filtered_delays)

        # 4. Error Rate (Typo detection)
        common_commands = {"ls", "cd", "pwd", "whoami", "cat", "grep", "ssh", "nmap", "sudo", "apt", "python", "rm", "mv", "cp", "mkdir"}
        typo_count = 0
        for cmd in session_commands:
            base_cmd = cmd.strip().split()[0].lower() if cmd.strip() else ""
            if not base_cmd:
                typo_count += 1
                continue
            
            # Detect common typos using a simple heuristic (len > 2 and not in common set)
            # This is a proxy for "mistakes" in a terminal environment
            if len(base_cmd) > 1 and base_cmd not in common_commands:
                # Basic check for common misspellings
                if base_cmd in ["sl", "gerp", "mkkdir", "pdw", "whami", "cta"]:
                    typo_count += 1
                elif any(err in cmd.lower() for err in self.error_indicators):
                    typo_count += 1

        error_rate = (typo_count / len(session_commands)) * 100 if session_commands else 0.0

        return {
            "raw_sequence": raw_sequence,
            "ngrams": ngrams,
            "avg_delay": avg_delay, # seconds
            "error_rate": error_rate # percentage
        }

    def _generate_ngrams(self, words: List[str], ns: List[int]) -> List[str]:
        """Helper to generate word-based n-grams."""
        all_ngrams = []
        for n in ns:
            for i in range(len(words) - n + 1):
                ngram = "_".join(words[i:i+n])
                all_ngrams.append(ngram)
        return all_ngrams
