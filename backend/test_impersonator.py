import os
import json
import numpy as np
from impersonator_detector import ImpersonatorDetector
from behavioral_trainer import train_user_models

def main():
    print("Running Impersonator End-to-End Test")
    
    # 1. Generate synthetic learning data
    print("Generating 35 synthetic learning samples...")
    detector = ImpersonatorDetector("test_session", "test_user_01")
    
    # Clear old data
    if os.path.exists('behavioral_samples.json'):
        os.remove('behavioral_samples.json')
    detector.sample_count = 0
        
    for i in range(35):
        # Normal typing speed (~120ms dwell)
        keystrokes = [{'key': 'A', 'dwell': np.random.normal(120, 10), 'flight': np.random.normal(90, 10)} for _ in range(10)]
        payload = {'keystrokes': keystrokes, 'files_accessed': ['auth.log'] if i == 0 else []}
        fv = detector.extract_features('keystroke', payload)
        detector.collect_sample(fv)
        
    print(f"Collected {detector.sample_count} samples.")
    
    # 2. Train Models
    print("Training ML Models...")
    train_user_models("test_user_01")
    print("Training Complete. Loading models...")
    detector.load_models()
    
    # 3. Test Normal Session
    print("\n--- SIMULATING NORMAL SESSION ---")
    keystrokes = [{'key': 'A', 'dwell': 125, 'flight': 95} for _ in range(10)]
    fv = detector.extract_features('keystroke', {'keystrokes': keystrokes})
    res = detector.scorer.score_action(fv)
    print(f"Normal Action Score: {res['irs']} ({res['severity']})")
    
    # 4. Test Impersonator Session (fast typing)
    print("\n--- SIMULATING IMPERSONATOR SESSION ---")
    keystrokes = [{'key': 'A', 'dwell': 60, 'flight': 40} for _ in range(10)]
    fv = detector.extract_features('keystroke', {'keystrokes': keystrokes})
    res = detector.scorer.score_action(fv)
    print(f"Impersonator Keystroke Score: {res['irs']} ({res['severity']})")
    
    # 5. Test Decoy Access
    print("\n--- SIMULATING DECOY FILE ACCESS ---")
    payload = {'files_accessed': ['/backend/decoys/passwords.xlsx']}
    fv = detector.extract_features('file_access', payload)
    res = detector.scorer.score_action(fv)
    print(f"Decoy Access Score: {res['irs']} ({res['severity']})")

if __name__ == "__main__":
    main()
