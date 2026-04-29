"""
LABYRINTH FORGE — Behavioral Fingerprint Dataset Generator
============================================================
Generates a realistic dataset of benign admin vs malicious hacker
behavioral fingerprints and saves to both CSV and Excel formats.
"""

import numpy as np
import pandas as pd
import os

np.random.seed(42)

N_SAMPLES = 1000
n_benign = N_SAMPLES // 2
n_malicious = N_SAMPLES - n_benign

# ── Benign Admins ─────────────────────────────────────
benign = pd.DataFrame({
    'avg_keystroke_delay_ms': np.random.normal(150, 30, n_benign),
    'typing_speed_wpm':       np.random.normal(60, 15, n_benign),
    'error_rate_pct':         np.random.normal(5, 2, n_benign),
    'command_diversity':      np.random.normal(0.7, 0.1, n_benign),
    'session_duration_s':     np.random.normal(1800, 600, n_benign),
    'unique_commands':        np.random.randint(5, 20, n_benign).astype(float),
    'dangerous_cmd_ratio':    np.random.normal(0.05, 0.02, n_benign),
    'time_between_commands_ms': np.random.normal(3000, 1000, n_benign),
    'backspace_frequency':    np.random.normal(0.08, 0.03, n_benign),
    'paste_frequency':        np.random.normal(0.1, 0.05, n_benign),
})
benign['label'] = 0
benign['label_name'] = 'Benign_Admin'
benign['frustration_index'] = np.random.normal(20, 10, n_benign)

# ── Malicious Hackers ─────────────────────────────────
malicious = pd.DataFrame({
    'avg_keystroke_delay_ms': np.random.normal(80, 40, n_malicious),
    'typing_speed_wpm':       np.random.normal(90, 25, n_malicious),
    'error_rate_pct':         np.random.normal(15, 5, n_malicious),
    'command_diversity':      np.random.normal(0.3, 0.15, n_malicious),
    'session_duration_s':     np.random.normal(600, 300, n_malicious),
    'unique_commands':        np.random.randint(15, 50, n_malicious).astype(float),
    'dangerous_cmd_ratio':    np.random.normal(0.4, 0.15, n_malicious),
    'time_between_commands_ms': np.random.normal(1000, 500, n_malicious),
    'backspace_frequency':    np.random.normal(0.2, 0.08, n_malicious),
    'paste_frequency':        np.random.normal(0.35, 0.1, n_malicious),
})
malicious['label'] = 1
malicious['label_name'] = 'Malicious_Hacker'
malicious['frustration_index'] = np.random.normal(60, 20, n_malicious)

# ── Combine & Clean ───────────────────────────────────
df = pd.concat([benign, malicious]).reset_index(drop=True)
for col in df.columns:
    if col not in ('label', 'label_name'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].clip(lower=0)
df['frustration_index'] = df['frustration_index'].clip(0, 100)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # Shuffle

# ── Save ──────────────────────────────────────────────
os.makedirs('datasets', exist_ok=True)

csv_path = os.path.join('datasets', 'behavioral_fingerprints.csv')
xlsx_path = os.path.join('datasets', 'behavioral_fingerprints.xlsx')

df.to_csv(csv_path, index=False)
df.to_excel(xlsx_path, index=False, sheet_name='Fingerprints')

print(f"[+] Dataset generated: {len(df)} samples ({n_benign} benign, {n_malicious} malicious)")
print(f"[+] Saved CSV:   {os.path.abspath(csv_path)}")
print(f"[+] Saved Excel: {os.path.abspath(xlsx_path)}")
print(f"\n[+] Columns: {list(df.columns)}")
print(f"[+] Shape:   {df.shape}")
print(f"\n--- Sample (first 5 rows) ---")
print(df.head().to_string())
