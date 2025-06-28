import os
import pickle
import pandas as pd
from sklearn.cluster import KMeans
from utils.db import engine
from utils.preprocessing import preprocess
from sqlalchemy import text

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

def train_and_save_kmeans():
    with engine.connect() as conn:
        table_names = conn.exec_driver_sql("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'dataset_%'
        """).fetchall()

        dfs = []
        for (table_name,) in table_names:
            df = pd.read_sql_table(table_name, con=engine)
            df_clean = preprocess(df)
            dfs.append(df_clean)

        if not dfs:
            raise ValueError("Tidak ada dataset untuk pelatihan.")

        all_data = pd.concat(dfs, ignore_index=True)
        features = all_data[['RataRataHarga', 'RataRataHargaTertinggiDiPasar']]

        model = KMeans(n_clusters=3, random_state=42)
        model.fit(features)

        with open(os.path.join(MODELS_DIR, "kmeans_model.pkl"), "wb") as f:
            pickle.dump(model, f)

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

    with open(os.path.join(MODELS_DIR, "kmeans_model.pkl"), "wb") as f:
        pickle.dump(model, f)
