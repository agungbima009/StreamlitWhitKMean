from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd

engine = create_engine("sqlite:///data/files.db")

def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                uploaded_at TEXT
            )
        """))

def save_file_metadata(file_name):
    now = datetime.now()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO uploaded_files (file_name, uploaded_at)
            VALUES (:f, :t)
        """), {"f": file_name, "t": now.isoformat()})
        result = conn.execute(text("SELECT last_insert_rowid()"))
        return result.fetchone()[0]

def save_dataset(file_id, df):
    df.to_sql(f"dataset_{file_id}", con=engine, index=False, if_exists="replace")
