import numpy as np

class KeystrokeAnalyzer:
    """
    Extracts timing features from raw keystroke events.
    """
    def __init__(self):
        pass
        
    def extract_features(self, keystrokes: list) -> list:
        """
        Expects a list of dicts: [{'key': 'A', 'dwell': 120, 'flight': 50}, ...]
        Returns an 8-dimensional feature vector.
        """
        if not keystrokes:
            return [0.0] * 8
            
        dwells = [k.get('dwell', 0) for k in keystrokes]
        flights = [k.get('flight', 0) for k in keystrokes]
        
        # 1 & 2: Mean and Std Dwell
        mean_dwell = float(np.mean(dwells)) if dwells else 0.0
        std_dwell = float(np.std(dwells)) if len(dwells) > 1 else 0.0
        
        # 3 & 4: Mean and Std Flight
        mean_flight = float(np.mean(flights)) if flights else 0.0
        std_flight = float(np.std(flights)) if len(flights) > 1 else 0.0
        
        # 5: Backspace frequency
        backspaces = sum(1 for k in keystrokes if k.get('key') == 'Backspace')
        backspace_freq = backspaces / len(keystrokes)
        
        # 6: Pause frequency (>500ms flight time)
        pauses = sum(1 for f in flights if f > 500)
        pause_freq = pauses / len(keystrokes)
        
        # 7: Burst typing ratio (<50ms flight time)
        bursts = sum(1 for f in flights if f < 50)
        burst_ratio = bursts / len(keystrokes)
        
        # 8: Enter-to-enter time (approximated here by total command time)
        enter_time = sum(dwells) + sum(flights)
        
        return [
            mean_dwell,
            std_dwell,
            mean_flight,
            std_flight,
            backspace_freq,
            pause_freq,
            burst_ratio,
            enter_time
        ]
