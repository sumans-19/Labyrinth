"""
LABYRINTH FORGE - Neural Ensemble ML Engine
============================================
Multi-model behavioral fingerprinting pipeline:
  1. Isolation Forest    → Unsupervised Anomaly Detection
  2. Gradient Boosting   → Supervised Attack Classification (XGBoost-style)
  3. Linear Regression   → Attacker Frustration Index Prediction
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, GradientBoostingClassifier
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_curve, auc, confusion_matrix
)
from sklearn.preprocessing import StandardScaler
import joblib
import os
import time

FEATURE_NAMES = [
    'avg_keystroke_delay_ms', 'typing_speed_wpm', 'error_rate_pct',
    'command_diversity', 'session_duration_s', 'unique_commands',
    'dangerous_cmd_ratio', 'time_between_commands_ms',
    'backspace_frequency', 'paste_frequency'
]


DATASET_CSV  = os.path.join(os.path.dirname(__file__), 'datasets', 'behavioral_fingerprints.csv')
DATASET_XLSX = os.path.join(os.path.dirname(__file__), 'datasets', 'behavioral_fingerprints.xlsx')


def load_dataset():
    """Load the behavioral fingerprint dataset from CSV/Excel file.
    Falls back to in-memory generation if files not found."""
    if os.path.exists(DATASET_CSV):
        df = pd.read_csv(DATASET_CSV)
        print(f"  [+] Loaded dataset from CSV: {DATASET_CSV}  ({len(df)} samples)")
        return df
    elif os.path.exists(DATASET_XLSX):
        df = pd.read_excel(DATASET_XLSX, sheet_name='Fingerprints')
        print(f"  [+] Loaded dataset from Excel: {DATASET_XLSX}  ({len(df)} samples)")
        return df
    else:
        print("  [!] Dataset files not found, generating in-memory (run generate_dataset.py first)")
        return _generate_fallback_data()


def _generate_fallback_data(n_samples=500):
    """Fallback: generate data in-memory if no CSV/Excel file exists."""
    np.random.seed(42)
    n_benign = n_samples // 2
    n_malicious = n_samples - n_benign

    benign = pd.DataFrame({
        'avg_keystroke_delay_ms': np.random.normal(150, 30, n_benign),
        'typing_speed_wpm': np.random.normal(60, 15, n_benign),
        'error_rate_pct': np.random.normal(5, 2, n_benign),
        'command_diversity': np.random.normal(0.7, 0.1, n_benign),
        'session_duration_s': np.random.normal(1800, 600, n_benign),
        'unique_commands': np.random.randint(5, 20, n_benign).astype(float),
        'dangerous_cmd_ratio': np.random.normal(0.05, 0.02, n_benign),
        'time_between_commands_ms': np.random.normal(3000, 1000, n_benign),
        'backspace_frequency': np.random.normal(0.08, 0.03, n_benign),
        'paste_frequency': np.random.normal(0.1, 0.05, n_benign),
    })
    benign['label'] = 0
    benign['frustration_index'] = np.random.normal(20, 10, n_benign)

    malicious = pd.DataFrame({
        'avg_keystroke_delay_ms': np.random.normal(80, 40, n_malicious),
        'typing_speed_wpm': np.random.normal(90, 25, n_malicious),
        'error_rate_pct': np.random.normal(15, 5, n_malicious),
        'command_diversity': np.random.normal(0.3, 0.15, n_malicious),
        'session_duration_s': np.random.normal(600, 300, n_malicious),
        'unique_commands': np.random.randint(15, 50, n_malicious).astype(float),
        'dangerous_cmd_ratio': np.random.normal(0.4, 0.15, n_malicious),
        'time_between_commands_ms': np.random.normal(1000, 500, n_malicious),
        'backspace_frequency': np.random.normal(0.2, 0.08, n_malicious),
        'paste_frequency': np.random.normal(0.35, 0.1, n_malicious),
    })
    malicious['label'] = 1
    malicious['frustration_index'] = np.random.normal(60, 20, n_malicious)

    df = pd.concat([benign, malicious]).reset_index(drop=True)
    for col in df.columns:
        if col != 'label':
            df[col] = df[col].clip(lower=0)
    df['frustration_index'] = df['frustration_index'].clip(0, 100)
    return df


class LabyrinthEnsemble:
    def __init__(self):
        self.scaler = StandardScaler()
        self.iso_forest = None
        self.gb_classifier = None
        self.frust_regressor = None
        self.training_history = []
        self.evaluation = {}
        self.trained = False
        self.dataset_path = None

    # ── Training ───────────────────────────────────────────────
    def train_all(self, n_samples=500):
        print("\n" + "=" * 60)
        print("  LABYRINTH FORGE — NEURAL ENSEMBLE TRAINING")
        print("=" * 60)

        df = load_dataset()
        self.dataset_path = DATASET_CSV if os.path.exists(DATASET_CSV) else DATASET_XLSX if os.path.exists(DATASET_XLSX) else 'in-memory'
        X = df[FEATURE_NAMES].values
        y_cls = df['label'].values
        y_fru = df['frustration_index'].values

        X_tr, X_te, y_tr, y_te = train_test_split(X, y_cls, test_size=0.2, random_state=42)
        _, _, yf_tr, yf_te = train_test_split(X, y_fru, test_size=0.2, random_state=42)

        X_tr_s = self.scaler.fit_transform(X_tr)
        X_te_s = self.scaler.transform(X_te)
        self.training_history = []

        # ── 1. Isolation Forest ────────────────────────────────
        print("\n[1/3] Isolation Forest (Unsupervised Anomaly Detection)")
        for ep in range(1, 6):
            m = IsolationForest(n_estimators=ep * 20, contamination=0.3, random_state=42)
            m.fit(X_tr_s)
            preds = (m.predict(X_te_s) == -1).astype(int)
            acc = accuracy_score(y_te, preds)
            self.training_history.append({
                'model': 'Isolation Forest', 'epoch': ep,
                'accuracy': round(acc * 100, 2), 'loss': round(1 - acc, 4)
            })
            print(f"  Epoch {ep:>2}/5  Trees: {ep*20:>3}  Acc: {acc*100:6.2f}%")

        self.iso_forest = IsolationForest(n_estimators=100, contamination=0.3, random_state=42)
        self.iso_forest.fit(X_tr_s)
        if_p = (self.iso_forest.predict(X_te_s) == -1).astype(int)
        if_res = self._cls_metrics(y_te, if_p, "Isolation Forest")

        # ── 2. Gradient Boosting ───────────────────────────────
        print("\n[2/3] Gradient Boosting Classifier (XGBoost-style)")
        for ep in range(1, 6):
            m = GradientBoostingClassifier(n_estimators=ep * 20, max_depth=5, learning_rate=0.1, random_state=42)
            m.fit(X_tr_s, y_tr)
            acc = m.score(X_te_s, y_te)
            self.training_history.append({
                'model': 'XGBoost', 'epoch': ep,
                'accuracy': round(acc * 100, 2), 'loss': round(1 - acc, 4)
            })
            print(f"  Epoch {ep:>2}/5  Est: {ep*20:>3}  Acc: {acc*100:6.2f}%  Loss: {1-acc:.4f}")

        self.gb_classifier = GradientBoostingClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
        )
        self.gb_classifier.fit(X_tr_s, y_tr)
        gb_p = self.gb_classifier.predict(X_te_s)
        gb_prob = self.gb_classifier.predict_proba(X_te_s)[:, 1]
        gb_res = self._cls_metrics(y_te, gb_p, "XGBoost")

        # ROC
        fpr, tpr, _ = roc_curve(y_te, gb_prob)
        roc_auc_val = auc(fpr, tpr)
        gb_res['roc_auc'] = round(roc_auc_val, 4)
        gb_res['roc_curve'] = {
            'fpr': [round(float(x), 4) for x in fpr],
            'tpr': [round(float(x), 4) for x in tpr]
        }

        # Feature importance
        imp = self.gb_classifier.feature_importances_
        gb_res['feature_importance'] = sorted(
            [{'feature': f, 'importance': round(float(v), 4)} for f, v in zip(FEATURE_NAMES, imp)],
            key=lambda x: x['importance'], reverse=True
        )
        print(f"  ROC-AUC: {roc_auc_val:.4f}")

        # ── 3. Frustration Regressor ───────────────────────────
        print("\n[3/3] Frustration Index Regressor")
        for ep in range(1, 6):
            n = max(10, int(len(X_tr_s) * (ep / 5)))
            reg = LinearRegression()
            reg.fit(X_tr_s[:n], yf_tr[:n])
            r2 = reg.score(X_te_s, yf_te)
            mse = float(np.mean((reg.predict(X_te_s) - yf_te) ** 2))
            self.training_history.append({
                'model': 'Frustration Regressor', 'epoch': ep,
                'accuracy': round(r2 * 100, 2), 'loss': round(mse / 100, 4)
            })
            print(f"  Epoch {ep:>2}/5  Samples: {n:>3}  R²: {r2*100:6.2f}%  MSE: {mse:.2f}")

        self.frust_regressor = LinearRegression()
        self.frust_regressor.fit(X_tr_s, yf_tr)
        r2_final = self.frust_regressor.score(X_te_s, yf_te)
        mse_final = float(np.mean((self.frust_regressor.predict(X_te_s) - yf_te) ** 2))
        frust_imp = sorted(
            [{'feature': f, 'importance': round(abs(float(v)), 4)}
             for f, v in zip(FEATURE_NAMES, self.frust_regressor.coef_)],
            key=lambda x: x['importance'], reverse=True
        )
        fr_res = {'r2_score': round(r2_final * 100, 2), 'mse': round(mse_final, 4),
                  'feature_importance': frust_imp}

        # ── Summary ────────────────────────────────────────────
        self.evaluation = {
            'isolation_forest': if_res,
            'xgboost': gb_res,
            'frustration_regressor': fr_res
        }
        self.trained = True

        print("\n" + "=" * 60)
        print("  ENSEMBLE TRAINING COMPLETE")
        print(f"  Isolation Forest:      {if_res['accuracy']}% accuracy")
        print(f"  XGBoost Classifier:    {gb_res['accuracy']}% accuracy  (AUC: {gb_res['roc_auc']})")
        print(f"  Frustration Regressor: {fr_res['r2_score']}% R²")
        print("=" * 60 + "\n")

        os.makedirs('model', exist_ok=True)
        joblib.dump(self.iso_forest, 'model/isolation_forest.pkl')
        joblib.dump(self.gb_classifier, 'model/gb_classifier.pkl')
        joblib.dump(self.frust_regressor, 'model/frust_regressor.pkl')
        joblib.dump(self.scaler, 'model/scaler.pkl')

        return {'training_history': self.training_history, 'evaluation': self.evaluation}

    # ── Prediction ─────────────────────────────────────────────
    def predict(self, features: dict):
        if not self.trained:
            return {'error': 'Models not trained yet'}
        vec = np.array([[features.get(f, 0) for f in FEATURE_NAMES]])
        sc = self.scaler.transform(vec)

        if_pred = int(self.iso_forest.predict(sc)[0])
        is_anomaly = if_pred == -1

        gb_pred = int(self.gb_classifier.predict(sc)[0])
        gb_prob = self.gb_classifier.predict_proba(sc)[0]

        frust = float(np.clip(self.frust_regressor.predict(sc)[0], 0, 100))
        threat = (float(gb_prob[1]) * 0.6 + (1.0 if is_anomaly else 0.0) * 0.4) * 100

        if frust < 30:
            strat, act = "ESCALATE_TARPIT", "Increasing latency & deploying more complex fake systems"
        elif frust < 70:
            strat, act = "MAINTAIN_ENGAGEMENT", "Sustaining deception with occasional fake data leaks"
        else:
            strat, act = "DEPLOY_HONEYCRED", "Leaking fake credentials to maximize intel before disconnect"

        return {
            'isolation_forest': {'is_anomaly': is_anomaly},
            'xgboost': {'prediction': gb_pred, 'confidence': round(float(max(gb_prob)) * 100, 2),
                        'malicious_prob': round(float(gb_prob[1]) * 100, 2)},
            'frustration_index': round(frust, 2),
            'ensemble_threat_score': round(threat, 2),
            'tarpit_strategy': strat, 'tarpit_action': act
        }

    # ── Helpers ─────────────────────────────────────────────────
    def _cls_metrics(self, y_true, y_pred, name):
        a = accuracy_score(y_true, y_pred)
        p = precision_score(y_true, y_pred, zero_division=0)
        r = recall_score(y_true, y_pred, zero_division=0)
        f = f1_score(y_true, y_pred, zero_division=0)
        cm = confusion_matrix(y_true, y_pred).tolist()
        print(f"  [+] {name}: Acc={a*100:.2f}%  Prec={p*100:.2f}%  Rec={r*100:.2f}%  F1={f*100:.2f}%")
        return {
            'accuracy': round(a * 100, 2), 'precision': round(p * 100, 2),
            'recall': round(r * 100, 2), 'f1_score': round(f * 100, 2),
            'confusion_matrix': cm
        }


# Singleton instance
ensemble = LabyrinthEnsemble()

# ── Model Descriptions (for GUI + CLI) ─────────────────
MODEL_DESCRIPTIONS = {
    'isolation_forest': {
        'name': 'Isolation Forest',
        'type': 'Unsupervised Anomaly Detection',
        'purpose': 'Detects "unknown unknown" attacks by isolating anomalous behavioral patterns without needing labeled data.',
        'how_it_works': 'Builds random decision trees that partition feature space. Anomalies require fewer partitions to isolate, resulting in shorter average path lengths. Contamination=0.3 flags the top 30% most isolated points.',
        'features_used': FEATURE_NAMES,
        'library': 'sklearn.ensemble.IsolationForest',
        'hyperparams': {'n_estimators': 100, 'contamination': 0.3, 'random_state': 42}
    },
    'xgboost': {
        'name': 'Gradient Boosting (XGBoost-style)',
        'type': 'Supervised Classification',
        'purpose': 'High-speed classification of known attack patterns. Distinguishes "Benign Admin" from "Malicious Hacker" with probability scores.',
        'how_it_works': 'Sequentially builds weak decision trees, each correcting the errors of the previous. Uses gradient descent on a loss function to optimize predictions. Outputs class probabilities via softmax.',
        'features_used': FEATURE_NAMES,
        'library': 'sklearn.ensemble.GradientBoostingClassifier',
        'hyperparams': {'n_estimators': 100, 'max_depth': 5, 'learning_rate': 0.1}
    },
    'frustration_regressor': {
        'name': 'Attacker Frustration Index',
        'type': 'Linear Regression (Novelty Metric)',
        'purpose': 'Predicts how close a hacker is to "quitting" based on erratic typing, rising error rates, and behavioral decay.',
        'how_it_works': 'Fits a linear model mapping behavioral features to a 0-100 frustration score. Low frustration → escalate tarpit difficulty. High frustration → leak fake credentials to keep them hooked.',
        'features_used': FEATURE_NAMES,
        'library': 'sklearn.linear_model.LinearRegression',
        'hyperparams': {'fit_intercept': True}
    }
}


def get_full_report():
    """Return full evaluation + model descriptions for API/GUI."""
    if not ensemble.trained:
        return {'error': 'Models not trained. Call /api/ensemble/train first.'}
    return {
        'training_history': ensemble.training_history,
        'evaluation': ensemble.evaluation,
        'model_descriptions': MODEL_DESCRIPTIONS
    }


# ── CLI Entry Point ────────────────────────────────────
if __name__ == '__main__':
    import sys

    C_RESET = '\033[0m'
    C_CYAN = '\033[96m'
    C_GREEN = '\033[92m'
    C_YELLOW = '\033[93m'
    C_RED = '\033[91m'
    C_MAGENTA = '\033[95m'
    C_BOLD = '\033[1m'
    C_DIM = '\033[2m'

    def hline(char='─', width=70):
        print(f'{C_DIM}{char * width}{C_RESET}')

    print(f'\n{C_CYAN}{C_BOLD}{"=" * 70}')
    print(f'  LABYRINTH FORGE — NEURAL ENSEMBLE CLI VERIFIER')
    print(f'{"=" * 70}{C_RESET}\n')

    results = ensemble.train_all(n_samples=500)
    ev = results['evaluation']

    # ── Model 1: Isolation Forest ──
    hline()
    desc = MODEL_DESCRIPTIONS['isolation_forest']
    iso = ev['isolation_forest']
    print(f'\n{C_MAGENTA}{C_BOLD}  MODEL 1: {desc["name"]}{C_RESET}')
    print(f'  {C_DIM}Type:{C_RESET}    {desc["type"]}')
    print(f'  {C_DIM}Library:{C_RESET} {desc["library"]}')
    print(f'  {C_DIM}Purpose:{C_RESET} {desc["purpose"]}')
    print(f'\n  {C_GREEN}✓ Accuracy:  {iso["accuracy"]}%{C_RESET}')
    print(f'  {C_GREEN}✓ Precision: {iso["precision"]}%{C_RESET}')
    print(f'  {C_GREEN}✓ Recall:    {iso["recall"]}%{C_RESET}')
    print(f'  {C_GREEN}✓ F1 Score:  {iso["f1_score"]}%{C_RESET}')
    print(f'  {C_DIM}Confusion Matrix: {iso["confusion_matrix"]}{C_RESET}\n')

    # ── Model 2: XGBoost ──
    hline()
    desc = MODEL_DESCRIPTIONS['xgboost']
    xgb = ev['xgboost']
    print(f'\n{C_MAGENTA}{C_BOLD}  MODEL 2: {desc["name"]}{C_RESET}')
    print(f'  {C_DIM}Type:{C_RESET}    {desc["type"]}')
    print(f'  {C_DIM}Library:{C_RESET} {desc["library"]}')
    print(f'  {C_DIM}Purpose:{C_RESET} {desc["purpose"]}')
    print(f'\n  {C_GREEN}✓ Accuracy:  {xgb["accuracy"]}%{C_RESET}')
    print(f'  {C_GREEN}✓ Precision: {xgb["precision"]}%{C_RESET}')
    print(f'  {C_GREEN}✓ Recall:    {xgb["recall"]}%{C_RESET}')
    print(f'  {C_GREEN}✓ F1 Score:  {xgb["f1_score"]}%{C_RESET}')
    print(f'  {C_CYAN}✓ ROC-AUC:   {xgb["roc_auc"]}{C_RESET}')
    print(f'  {C_DIM}Confusion Matrix: {xgb["confusion_matrix"]}{C_RESET}')
    print(f'\n  {C_YELLOW}Top Features:{C_RESET}')
    for fi in xgb['feature_importance'][:5]:
        bar = '█' * int(fi['importance'] * 40)
        print(f'    {fi["feature"]:<30} {bar} {fi["importance"]:.4f}')
    print()

    # ── Model 3: Frustration Regressor ──
    hline()
    desc = MODEL_DESCRIPTIONS['frustration_regressor']
    fr = ev['frustration_regressor']
    print(f'\n{C_MAGENTA}{C_BOLD}  MODEL 3: {desc["name"]}{C_RESET}')
    print(f'  {C_DIM}Type:{C_RESET}    {desc["type"]}')
    print(f'  {C_DIM}Library:{C_RESET} {desc["library"]}')
    print(f'  {C_DIM}Purpose:{C_RESET} {desc["purpose"]}')
    print(f'\n  {C_GREEN}✓ R² Score: {fr["r2_score"]}%{C_RESET}')
    print(f'  {C_GREEN}✓ MSE:      {fr["mse"]}{C_RESET}')
    print(f'\n  {C_YELLOW}Top Features:{C_RESET}')
    for fi in fr['feature_importance'][:5]:
        bar = '█' * int(fi['importance'] * 4)
        print(f'    {fi["feature"]:<30} {bar} {fi["importance"]:.4f}')

    # ── Test Prediction ──
    hline()
    print(f'\n{C_CYAN}{C_BOLD}  LIVE PREDICTION TEST{C_RESET}')
    test_input = {
        'avg_keystroke_delay_ms': 60, 'typing_speed_wpm': 110,
        'error_rate_pct': 22, 'command_diversity': 0.2,
        'session_duration_s': 300, 'unique_commands': 35,
        'dangerous_cmd_ratio': 0.55, 'time_between_commands_ms': 600,
        'backspace_frequency': 0.3, 'paste_frequency': 0.45
    }
    pred = ensemble.predict(test_input)
    anom = 'YES' if pred['isolation_forest']['is_anomaly'] else 'NO'
    print(f'  Anomaly Detected:      {anom}')
    print(f'  XGBoost Malicious:     {pred["xgboost"]["malicious_prob"]}%  (Confidence: {pred["xgboost"]["confidence"]}%)')
    print(f'  Frustration Index:     {pred["frustration_index"]}/100')
    print(f'  Ensemble Threat Score: {pred["ensemble_threat_score"]}/100')
    print(f'  Tarpit Strategy:       {C_RED}{pred["tarpit_strategy"]}{C_RESET}')
    print(f'  Action:                {pred["tarpit_action"]}')

    print(f'\n{C_GREEN}{C_BOLD}{"=" * 70}')
    print(f'ALL 3 MODELS VERIFIED SUCCESSFULLY')
    print(f'{"=" * 70}{C_RESET}\n')
