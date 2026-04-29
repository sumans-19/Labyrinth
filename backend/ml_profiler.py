import pandas as pd
import numpy as np
import os
import random
import string
import json
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any, Tuple, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/labrynth"
Base = declarative_base()

class AttackerProfile(Base):
    __tablename__ = 'attacker_profiles'
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100))
    attacker_profile = Column(String(200))
    raw_command_sequence = Column(Text)
    avg_time_delay_ms = Column(Float)
    error_rate_percentage = Column(Float)
    total_commands_executed = Column(Integer)
    target_objective = Column(Text)
    ip_address = Column(String(50), nullable=True)

class MLProfiler:
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 3), token_pattern=r'\b\w+\b', stop_words=None)
        self.profiles_df = None
        self.tfidf_matrix = None
        
        # Initialize AI
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.model = None
        
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                print(f"Gemini Init Error in Profiler: {e}")
        
        self.load_database()

    def load_database(self):
        try:
            session = self.Session()
            profiles = session.query(AttackerProfile).all()
            session.close()
            
            if profiles:
                data = []
                for p in profiles:
                    data.append({
                        'session_id': p.session_id,
                        'attacker_profile': p.attacker_profile,
                        'raw_command_sequence': p.raw_command_sequence.replace(',', ' ') if p.raw_command_sequence else "",
                        'avg_time_delay_ms': p.avg_time_delay_ms,
                        'error_rate_percentage': p.error_rate_percentage,
                        'total_commands_executed': p.total_commands_executed,
                        'target_objective': p.target_objective,
                        'ip_address': p.ip_address
                    })
                self.profiles_df = pd.DataFrame(data)
                self.profiles_df = self.profiles_df.dropna(subset=['raw_command_sequence'])
                
                if not self.profiles_df.empty:
                    self.tfidf_matrix = self.vectorizer.fit_transform(self.profiles_df['raw_command_sequence'])
            else:
                self.profiles_df = pd.DataFrame()
        except Exception as e:
            print(f"Error loading database: {e}")
            self.profiles_df = pd.DataFrame()

    def check_similarity(self, live_session_data: Dict[str, Any], attacker_ip: str = "Unknown") -> Tuple[bool, Optional[Dict[str, Any]], float]:
        raw_text = live_session_data.get("raw_sequence", "").replace(',', ' ')
        num_commands = len(raw_text.split())
        
        if num_commands < 2:
            return False, {"profile_id": "New Attacker", "objective": "Analyzing..."}, 0.0

        if self.profiles_df is None or self.profiles_df.empty or self.tfidf_matrix is None:
            return False, {"profile_id": "New Attacker", "objective": "First Session"}, 0.0

        try:
            live_vector = self.vectorizer.transform([raw_text])
            similarities = cosine_similarity(live_vector, self.tfidf_matrix).flatten()
            max_idx = np.argmax(similarities)
            max_score = similarities[max_idx]
            
            if max_score > 0.70:
                match_row = self.profiles_df.iloc[max_idx]
                return True, {
                    "profile_id": match_row['attacker_profile'],
                    "objective": match_row['target_objective'],
                    "session_id": match_row['session_id']
                }, float(max_score)
            
            return False, {"profile_id": "New Attacker", "objective": "Pattern Not Recognized"}, float(max_score)
        except Exception as e:
            print(f"Similarity Error: {e}")
            return False, {"profile_id": "New Attacker", "objective": "Error"}, 0.0

    def generate_new_profile(self, data: Dict[str, Any], ip: str) -> Optional[Dict[str, Any]]:
        raw_seq = data.get("raw_sequence", "")
        
        prompt = f"""
        Analyze the following terminal command sequence:
        '{raw_seq}'
        
        Generate:
        1. A unique, cool attacker profile name (e.g., 'Ghost_Protocol', 'Shadow_Byte').
        2. A concise 'Target Objective' (e.g., 'Credential Harvesting', 'System Enumeration').
        
        Return ONLY a JSON object:
        {{"profile_name": "...", "objective": "..."}}
        """
        
        profile_name = f"Threat_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
        objective = "Manual Inspection Required"

        try:
            if self.model:
                response = self.model.generate_content(prompt)
                if response and response.text:
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    ai_data = json.loads(clean_text)
                    profile_name = ai_data.get("profile_name", profile_name)
                    objective = ai_data.get("objective", objective)
            elif self.groq_key:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
                payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
                resp = requests.post(url, json=payload, headers=headers, timeout=10)
                if resp.status_code == 200:
                    ai_data = json.loads(resp.json()['choices'][0]['message']['content'])
                    profile_name = ai_data.get("profile_name", profile_name)
                    objective = ai_data.get("objective", objective)
                elif resp.status_code == 429:
                    print("[!] Profiler: Groq Rate Limit Reached.")
        except Exception as e:
            if "403" in str(e):
                print("[!] Profiler: Gemini 403 Error (Permission Denied). Disabling Gemini.")
                self.model = None
            else:
                print(f"AI Generation Error in Profiler: {e}")

        try:
            session = self.Session()
            new_p = AttackerProfile(
                session_id=f"S_NEW_{random.randint(1000,9999)}",
                attacker_profile=profile_name,
                raw_command_sequence=raw_seq,
                avg_time_delay_ms=round(data.get("avg_delay", 0.0) * 1000, 2),
                error_rate_percentage=round(data.get("error_rate", 0.0), 2),
                total_commands_executed=len(raw_seq.split()),
                target_objective=objective,
                ip_address=ip
            )
            session.add(new_p)
            session.commit()
            session.close()
            self.load_database()
            return {"profile_id": profile_name, "objective": objective}
        except Exception as e:
            print(f"DB Save Error: {e}")
            return None
