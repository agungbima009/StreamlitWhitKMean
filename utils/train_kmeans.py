import os
import pickle
import shutil
import pandas as pd
from datetime import datetime
from sklearn.cluster import KMeans
from sqlalchemy import text
from utils.db import engine
from utils.preprocessing import preprocess

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

def log_model_training(file_ids, model_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_ids_str = ",".join(str(fid) for fid in file_ids)

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_training_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trained_at TEXT,
                file_ids TEXT,
                model_path TEXT
            )
        """))
        conn.execute(text("""
            INSERT INTO model_training_logs (trained_at, file_ids, model_path)
            VALUES (:trained_at, :file_ids, :model_path)
        """), {
            "trained_at": timestamp,
            "file_ids": file_ids_str,
            "model_path": model_path
        })

def train_and_save_kmeans():
    with engine.connect() as conn:
        table_names = conn.exec_driver_sql("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'dataset_%'
        """).fetchall()

    dfs = []
    file_ids = []
    for (table_name,) in table_names:
        df = pd.read_sql_table(table_name, con=engine)
        df_clean = preprocess(df)
        dfs.append(df_clean)
        file_ids.append(table_name.replace("dataset_", ""))

    if not dfs:
        raise ValueError("Tidak ada dataset untuk pelatihan.")

    all_data = pd.concat(dfs, ignore_index=True)
    features = all_data[['RataRataHarga', 'RataRataHargaTertinggiDiPasar']]

    model = KMeans(n_clusters=3, random_state=42)
    model.fit(features)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    model_path = os.path.join(MODELS_DIR, f"kmeans_model_{timestamp}.pkl")

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    # Salin juga ke model utama
    shutil.copy(model_path, os.path.join(MODELS_DIR, "kmeans_model.pkl"))

    log_model_training(file_ids, model_path)

def train_kmeans_with_selected_files(file_ids):
    dfs = []
    for file_id in file_ids:
        table_name = f"dataset_{file_id}"
        df = pd.read_sql_table(table_name, con=engine)
        df_clean = preprocess(df)
        dfs.append(df_clean)

    if not dfs:
        raise ValueError("Tidak ada dataset terpilih untuk pelatihan.")

    all_data = pd.concat(dfs, ignore_index=True)
    features = all_data[['RataRataHarga', 'RataRataHargaTertinggiDiPasar']]

    model = KMeans(n_clusters=3, random_state=42)
    model.fit(features)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    model_path = os.path.join(MODELS_DIR, f"kmeans_model_{timestamp}.pkl")

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    # Salin ke versi utama juga
    shutil.copy(model_path, os.path.join(MODELS_DIR, "kmeans_model.pkl"))

    log_model_training(file_ids, model_path)
