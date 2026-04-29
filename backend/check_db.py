import sqlalchemy
from sqlalchemy import create_engine, inspect

DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/labrynth"

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables in 'labrynth': {tables}")
    
    if "attacker_profiles" in tables:
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT count(*) FROM attacker_profiles"))
            count = result.scalar()
            print(f"Rows in 'attacker_profiles': {count}")
            
            if count > 0:
                result = conn.execute(sqlalchemy.text("SELECT * FROM attacker_profiles LIMIT 1"))
                row = result.fetchone()
                print(f"First row: {row}")
except Exception as e:
    print(f"Error: {e}")
