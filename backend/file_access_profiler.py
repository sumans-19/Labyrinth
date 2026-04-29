import os

class FileAccessProfiler:
    """
    Extracts sequence and behavioral features from file accesses.
    """
    def __init__(self, profile=None):
        self.profile = profile or {}
        
    def extract_features(self, payload: dict, is_training: bool = False) -> list:
        """
        Expects payload: {'files_accessed': ['/etc/passwd'], 'time_since_last': 1200}
        Returns an 8-dimensional feature vector.
        """
        files = payload.get('files_accessed', [])
        time_since_last = payload.get('time_since_last', 0)
        
        if not files:
            return [0.0] * 8
            
        first_file = files[0]
        
        # 1: First file match
        expected_first = self.profile.get('first_file', '')
        first_file_match = 1.0 if (not is_training and first_file == expected_first) else 0.0
        if is_training: first_file_match = 1.0
        
        # 2: File sequence score (simplified edit distance mock for real-time)
        file_sequence_score = 1.0 if is_training else 0.5
        
        # 3: Novel file access ratio
        known_files = set(self.profile.get('known_files', []))
        novel_files = sum(1 for f in files if f not in known_files)
        novel_file_ratio = novel_files / len(files) if not is_training else 0.0
        
        # 4: Decoy file trigger (CRITICAL)
        decoy_file_flag = 1.0 if any('decoys' in f or 'honey' in f.lower() for f in files) else 0.0
        
        # 5: Sensitive file affinity
        sensitive_keywords = ['passwd', 'shadow', '.env', 'secret', 'key', 'config', 'id_rsa']
        sensitive_count = sum(1 for f in files if any(k in f.lower() for k in sensitive_keywords))
        sensitive_file_affinity = sensitive_count / len(files)
        
        # 6: Inter-file timing
        inter_file_timing = time_since_last
        
        # 7: Directory breadth
        directories = set(os.path.dirname(f) for f in files)
        directory_breadth = float(len(directories))
        
        # 8: File type deviation (simplified)
        file_type_deviation = 0.0 if is_training else 0.2
        
        return [
            first_file_match,
            file_sequence_score,
            novel_file_ratio,
            decoy_file_flag,
            sensitive_file_affinity,
            float(inter_file_timing),
            directory_breadth,
            file_type_deviation
        ]
