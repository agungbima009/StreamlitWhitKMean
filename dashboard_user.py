import streamlit as st
import pandas as pd
# from sqlalchemy import create_engine
from utils.db import init_db, engine
from utils.preprocessing import preprocess
from utils.visualizations import show_scorecard, show_clustermap, show_top_bottom_locations, show_price_trend, show_data_table
import pickle

model = pickle.load(open("models/kmeans_model.pkl", "rb"))

init_db()

def load_dataset(file_id):
    return pd.read_sql_table(f"dataset_{file_id}", con=engine)


def render():
    st.markdown(
    """
    <h1 style='text-align: center; 
               margin-bottom: 50px;
               padding-bottom: 50px;
               margin-top: 0px;'>
    Visualisasi Harga Beras Medium Jawa Timur
    </h1>
    """, 
    unsafe_allow_html=True
)

    files = pd.read_sql("SELECT * FROM uploaded_files ORDER BY uploaded_at DESC", engine)
    if files.empty:
        st.warning("Belum ada data yang diunggah admin.")
        return

    file_dict = {f"{row['file_name']} ({row['uploaded_at'][:19]})": row['id'] for _, row in files.iterrows()}
    selected_label = st.sidebar.selectbox("Pilih Dataset:", list(file_dict.keys()))
    selected_file_id = file_dict.get(selected_label)

    if selected_file_id is None:
        st.warning("Silakan pilih dataset terlebih dahulu.")
        return

    df = load_dataset(selected_file_id)
    df_clean = preprocess(df)
    df_clean["cluster"] = model.predict(df_clean[["RataRataHarga", "RataRataHargaTertinggiDiPasar"]])

    # Filter Cluster di Sidebar
    cluster_options = sorted(df_clean["cluster"].unique())
    selected_cluster = st.sidebar.multiselect("Pilih Cluster:", options=cluster_options, default=cluster_options)

    # Filter Lokasi di Sidebar
    lokasi_options = sorted(df_clean["Lokasi"].unique()) if "Lokasi" in df_clean.columns else []
    selected_lokasi = st.sidebar.multiselect("Pilih Lokasi:", options=lokasi_options, default=lokasi_options)

    filtered_df = df_clean[
        (df_clean["cluster"].isin(selected_cluster)) &
        (df_clean["Lokasi"].isin(selected_lokasi))
    ]

    show_scorecard(filtered_df)
    show_clustermap(filtered_df)
    show_top_bottom_locations(filtered_df)
    show_price_trend()
    show_data_table(filtered_df)