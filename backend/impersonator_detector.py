import json
import os
from keystroke_analyzer import KeystrokeAnalyzer
from file_access_profiler import FileAccessProfiler
from anomaly_scorer import RealTimeScorer

class ImpersonatorDetector:
    def __init__(self, session_id, user_id):
        self.session_id = session_id
        self.user_id = user_id
        self.sample_count = 0
        self.keystroke_analyzer = KeystrokeAnalyzer()
        self.file_profiler = FileAccessProfiler()
        self.scorer = None
        self.data_file = 'behavioral_samples.json'
        
        self._load_state()
        
    def _load_state(self):
        # Determine if we are in learning phase
        if not os.path.exists(self.data_file):
            self.sample_count = 0
        else:
            with open(self.data_file, 'r') as f:
                samples = json.load(f)
                self.sample_count = sum(1 for s in samples if s['user_id'] == self.user_id)
                
        if self.sample_count >= 15:
            try:
                self.scorer = RealTimeScorer(self.user_id)
            except Exception:
                pass # Model might not be trained yet
                
    def load_models(self):
        self.scorer = RealTimeScorer(self.user_id)
                
    def is_learning_phase(self):
        return self.sample_count < 15
        
    def _extract_command_features(self, payload: dict) -> list:
        # Simplified for demo: mock 8 features
        return [1.0, 1.0, 0.0, 0.0, 0.1, 0.0, 0.0, 1.0]

    def extract_features(self, event_type: str, payload: dict) -> list:
        # Return 24-dim vector
        v_keys = self.keystroke_analyzer.extract_features(payload.get('keystrokes', []))
        v_cmds = self._extract_command_features(payload)
        v_file = self.file_profiler.extract_features(payload, is_training=self.is_learning_phase())
        
        # Override file access features if it's a file event
        if event_type == 'file_access':
            v_file = self.file_profiler.extract_features(payload, is_training=self.is_learning_phase())
            
        return v_keys + v_cmds + v_file
        
    def collect_sample(self, feature_vector: list, raw_command=""):
        sample = {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': 0.0,
            'feature_vector': feature_vector,
            'raw_command': raw_command,
            'raw_files': ""
        }
        
        samples = []
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                try:
                    samples = json.load(f)
                except:
                    pass
        samples.append(sample)
        with open(self.data_file, 'w') as f:
            json.dump(samples, f)
            
        self.sample_count += 1
