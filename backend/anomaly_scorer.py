import os
import json
import numpy as np
import joblib

ISOLATION_FOREST_WEIGHT = 0.45
LSTM_WEIGHT             = 0.35  # Still using this variable name for sequence score weight
FILE_ACCESS_WEIGHT      = 0.20

def score_isolation_forest(model, scaler, feature_vector):
    X = scaler.transform([feature_vector])
    score = float(model.decision_function(X)[0])
    # Softer gradient: 0.15 is considered slightly normal, below that is anomalous
    risk = max(0, min(100, int((0.15 - score) * 300)))
    print(f"[DEBUG] Isolation Forest - Raw Score: {score:.4f} -> Risk: {risk}")
    return risk

def compute_irs(if_score, seq_score, file_score):
    irs = (
        if_score  * ISOLATION_FOREST_WEIGHT +
        seq_score * LSTM_WEIGHT +
        file_score * FILE_ACCESS_WEIGHT
    )
    return round(min(100, max(0, irs)), 2)

def classify_severity(irs):
    if irs < 40: return "NORMAL"
    if irs < 70: return "SUSPICIOUS"
    if irs < 85: return "WARNING"
    return "CRITICAL"

class RealTimeScorer:
    def __init__(self, user_id):
        model_dir = f'model/profiles/{user_id}'
        self.if_model = joblib.load(f'{model_dir}/isolation_forest.pkl')
        self.scaler   = joblib.load(f'{model_dir}/scaler.pkl')
        self.mlp      = joblib.load(f'{model_dir}/mlp_model.pkl')
        
        self.profile  = json.load(open(f'{model_dir}/profile.json'))
        self.sequence_buffer = []
        
        # Prefill sequence buffer with the last 10 training samples so MLP works immediately
        data_file = 'behavioral_samples.json'
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                all_samples = json.load(f)
                user_samples = [s['feature_vector'] for s in all_samples if s['user_id'] == user_id]
                if len(user_samples) >= 10:
                    self.sequence_buffer = user_samples[-10:]
        
    def score_action(self, feature_vector: list) -> dict:
        fv = np.array(feature_vector)
        
        if_score = score_isolation_forest(self.if_model, self.scaler, fv)
        
        self.sequence_buffer.append(fv)
        if len(self.sequence_buffer) >= 10:
            seq = np.array(self.sequence_buffer[-10:]).flatten()
            
            # Predict the next state (which is actually `fv` since we added it to buffer... wait)
            # Actually, `self.sequence_buffer[-10:]` includes the current action. 
            # So the input should be the 10 PREVIOUS actions to predict THIS action.
            # Let's fix that logic: we need 11 actions to have 10 inputs and 1 target.
            pass
        
        if len(self.sequence_buffer) > 10:
            # The 10 items before current action, scaled
            seq_scaled = self.scaler.transform(self.sequence_buffer)
            seq_in = np.array(seq_scaled[-11:-1]).flatten()
            predicted = self.mlp.predict([seq_in])[0]
            target = seq_scaled[-1]
            mse = float(np.mean((predicted - target) ** 2))
            
            # Since data is scaled (variance 1), MSE is stable.
            # Normal variations have an MSE around 0.5 - 2.0. 
            # We map MSE to a 0-100 risk score, capping at 100 if MSE > 6.0
            seq_score = min(100, int((mse / 6.0) * 100))
            print(f"[DEBUG] MLP Sequence - Scaled MSE: {mse:.4f} -> SeqScore: {seq_score}")
        else:
            seq_score = 0
            print(f"[DEBUG] MLP Sequence - Buffer size {len(self.sequence_buffer)} < 11, skipping")
            
        file_score = 100 if feature_vector[19] == 1.0 else 0
        if file_score == 100:
            return {
                'irs': 95,
                'if_score': if_score,
                'lstm_score': seq_score,
                'file_score': 100,
                'severity': "CRITICAL"
            }
            
        irs = compute_irs(if_score, seq_score, file_score)
        
        return {
            'irs': irs,
            'if_score': if_score,
            'lstm_score': seq_score,
            'file_score': file_score,
            'severity': classify_severity(irs)
        }
