import os
import json
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor

def augment_samples(X, n_augments=5):
    augmented = [X]
    for _ in range(n_augments):
        noise = np.random.normal(0, 0.05, X.shape)
        X_noisy = X + noise
        
        # Optionally shuffle a subset to simulate slightly out-of-order commands
        if len(X_noisy) > 10 and np.random.rand() > 0.5:
            import random
            idx = random.randint(0, len(X_noisy) - 2)
            # Swap two adjacent feature vectors
            temp = np.copy(X_noisy[idx])
            X_noisy[idx] = X_noisy[idx+1]
            X_noisy[idx+1] = temp
            
        augmented.append(X_noisy)
    return np.vstack(augmented)

def train_isolation_forest(feature_matrix):
    scaler = StandardScaler()
    X = scaler.fit_transform(feature_matrix)
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42
    )
    model.fit(X)
    return model, scaler

def build_sequences(X, window=10):
    seq_in, seq_out = [], []
    for i in range(len(X) - window):
        seq_in.append(X[i:i+window].flatten()) # Flatten window for MLP
        seq_out.append(X[i+window])
    return np.array(seq_in), np.array(seq_out)

def train_user_models(user_id: str, data_file: str = 'behavioral_samples.json'):
    if not os.path.exists(data_file):
        raise ValueError("No training data found.")
        
    with open(data_file, 'r') as f:
        all_samples = json.load(f)
        
    user_samples = [s['feature_vector'] for s in all_samples if s['user_id'] == user_id]
    if len(user_samples) < 30:
        raise ValueError(f"Need at least 30 samples, got {len(user_samples)}")
        
    X = np.array(user_samples)
    X_aug = augment_samples(X, n_augments=5)
    
    if_model, scaler = train_isolation_forest(X_aug)
    
    # Train Scikit-learn MLP Regressor for sequence prediction
    X_aug_scaled = scaler.transform(X_aug)
    X_in, X_out = build_sequences(X_aug_scaled, window=10)
    mlp_model = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        solver='adam',
        max_iter=500,
        random_state=42
    )
    
    if len(X_in) > 0:
        mlp_model.fit(X_in, X_out)
    else:
        # Fallback if extremely small dataset
        dummy_in = np.zeros((2, X.shape[1]*10))
        dummy_out = np.zeros((2, X.shape[1]))
        mlp_model.fit(dummy_in, dummy_out)

    # Save models
    model_dir = f'model/profiles/{user_id}'
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(if_model, f'{model_dir}/isolation_forest.pkl')
    joblib.dump(scaler, f'{model_dir}/scaler.pkl')
    joblib.dump(mlp_model, f'{model_dir}/mlp_model.pkl')
    
    profile = {'first_file': 'auth.log', 'known_files': []}
    with open(f'{model_dir}/profile.json', 'w') as f:
        json.dump(profile, f)
        
    return {'status': 'trained', 'samples': len(X), 'augmented': len(X_aug)}
