import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database Configuration
DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/labrynth"
EXCEL_PATH = "backend/LabyrinthForge_Attacker_Profiles_Dataset.xlsx"

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

def migrate():
    print(f"[*] Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    if not os.path.exists(EXCEL_PATH):
        print(f"[!] Excel file not found at {EXCEL_PATH}")
        return

    print(f"[*] Reading data from {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)
    
    # Rename columns to match DB if necessary, but according to previous inspection:
    # ['session_id', 'attacker_profile', 'raw_command_sequence', 'avg_time_delay_ms', 'error_rate_percentage', 'total_commands_executed', 'target_objective']
    
    count = 0
    for _, row in df.iterrows():
        # Check if already exists to avoid duplicates on re-run
        exists = session.query(AttackerProfile).filter_by(session_id=str(row['session_id'])).first()
        if not exists:
            profile = AttackerProfile(
                session_id=str(row['session_id']),
                attacker_profile=str(row['attacker_profile']),
                raw_command_sequence=str(row['raw_command_sequence']),
                avg_time_delay_ms=float(row['avg_time_delay_ms']),
                error_rate_percentage=float(row['error_rate_percentage']),
                total_commands_executed=int(row['total_commands_executed']),
                target_objective=str(row['target_objective'])
            )
            session.add(profile)
            count += 1
    
    session.commit()
    print(f"[+] Successfully migrated {count} new profiles to PostgreSQL.")
    session.close()

if __name__ == "__main__":
    migrate()
