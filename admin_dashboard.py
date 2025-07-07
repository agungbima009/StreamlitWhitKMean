import streamlit as st
import pandas as pd
import time
import os
import pickle
from sqlalchemy import text
from datetime import datetime

from utils.db import save_file_metadata, save_dataset, engine
from utils.preprocessing import preprocess, preprocess_initial
from utils.train_kmeans import train_and_save_kmeans, train_kmeans_with_selected_files
import utils.auth as auth

MODELS_DIR = "models"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def init_cluster_labels_table():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cluster_labels (
                cluster_id INTEGER PRIMARY KEY,
                label TEXT
            )
        """))

init_cluster_labels_table()

# Load KMeans model
kmeans_model_path = os.path.join(MODELS_DIR, "kmeans_model.pkl")
if os.path.exists(kmeans_model_path):
    kmeans_model = pickle.load(open(kmeans_model_path, "rb"))
else:
    kmeans_model = None

# Simpan label cluster visualisasi ke database
def save_cluster_labels(labels_dict):
    with engine.begin() as conn:
        for cluster_id, label in labels_dict.items():
            conn.execute(text("""
                INSERT INTO cluster_labels (cluster_id, label)
                VALUES (:cluster_id, :label)
                ON CONFLICT(cluster_id) DO UPDATE SET label = :label
            """), {"cluster_id": cluster_id, "label": label})

# Ambil label cluster visualisasi dari database
def load_cluster_labels():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT cluster_id, label FROM cluster_labels")).fetchall()
    return {row[0]: row[1] for row in result} if result else {0: "Tinggi", 1: "Sedang", 2: "Rendah"}

def log_model_training(file_ids):
    timestamp = datetime.now().isoformat()
    model_path = os.path.join(MODELS_DIR, "kmeans_model.pkl")
    file_ids_str = ",".join(map(str, file_ids))

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO model_training_logs (trained_at, file_ids, model_path)
            VALUES (:trained_at, :file_ids, :model_path)
        """), {
            "trained_at": timestamp,
            "file_ids": file_ids_str,
            "model_path": model_path
        })

def clear_model_training_logs():
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM model_training_logs"))

def show_model_training_history():
    st.subheader("📊 Histori Pelatihan Model KMeans")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, trained_at, file_ids, model_path
            FROM model_training_logs
            ORDER BY trained_at DESC
        """)).fetchall()

    if not result:
        st.info("Belum ada histori pelatihan model.")
        return

    df_history = pd.DataFrame(result, columns=["ID", "Waktu Pelatihan", "File Dataset", "Path Model"])
    df_history["Waktu Pelatihan"] = pd.to_datetime(df_history["Waktu Pelatihan"])

    latest = df_history.iloc[0]

    tab1, tab2 = st.tabs(["📌 Ringkasan Model Terbaru", "📜 Daftar Histori Pelatihan"])

    with tab1:
        st.markdown("#### Model Terakhir")
        col1, col2, col3 = st.columns(3)
        col1.metric("🕒 Waktu", latest["Waktu Pelatihan"].strftime("%d %B %Y %H:%M"))
        col2.metric("🧾 Jumlah File", len(latest["File Dataset"].split(",")))
        col3.metric("📀 Nama File", latest["Path Model"].split("/")[-1])

        st.markdown("**File Dataset yang Digunakan:**")
        st.code(latest["File Dataset"], language="bash")

        st.markdown("**Lokasi Model Disimpan:**")
        st.code(latest["Path Model"])

    with tab2:
        st.markdown("#### Semua Riwayat Pelatihan")
        st.dataframe(df_history, use_container_width=True)

        csv = df_history.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Riwayat Pelatihan (CSV)",
            data=csv,
            file_name="riwayat_pelatihan_model.csv",
            mime="text/csv"
        )

def get_cluster_label_map():
    try:
        return load_cluster_labels()
    except:
        return {0: "Tinggi", 1: "Sedang", 2: "Rendah"}

def render():
    if "cluster_labels" not in st.session_state:
        st.session_state.cluster_labels = load_cluster_labels()
    if "label_applied" not in st.session_state:
        st.session_state.label_applied = False

    if not st.session_state.get("authenticated"):
        st.warning("Silakan login terlebih dahulu.")
        return

    auth.logout()

    st.title("Admin Panel - Upload Data")

    st.subheader("📤 Upload Data Baru")
    uploaded_file = st.file_uploader("Upload File CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file, header=None)
        st.write("Data Awal:")
        st.dataframe(df.head())

        initial_df = preprocess_initial(df)
        st.write("Setelah Preprocessing Awal (struktur & rekap):")
        st.dataframe(initial_df.head())

        preprocessed_df = preprocess(initial_df)
        result_df = preprocessed_df.copy()

        if kmeans_model:
            result_df["cluster"] = kmeans_model.predict(result_df[["RataRataHarga", "RataRataHargaTertinggiDiPasar"]])
        else:
            st.warning("Model belum tersedia. Silakan reset model terlebih dahulu.")

        st.write("Hasil Preprocessing (winsorization):")
        st.dataframe(preprocessed_df.head())

        st.write("Perbandingan Perubahan Kolom:")
        cols_common = list(set(initial_df.columns) & set(preprocessed_df.columns))
        diff_report = []
        for col in cols_common:
            if not initial_df[col].equals(preprocessed_df[col]):
                changed = (initial_df[col] != preprocessed_df[col]).sum()
                diff_report.append((col, changed))
        if diff_report:
            diff_df = pd.DataFrame(diff_report, columns=["Kolom", "Jumlah Data Berubah"])
            st.dataframe(diff_df)
        else:
            st.info("Tidak ada perubahan terdeteksi pada kolom yang sama.")

        st.write("Hasil Clustering Preview:")
        st.dataframe(result_df)

        if st.button("Konfirmasi dan Simpan ke Database"):
            file_id = save_file_metadata(uploaded_file.name)
            save_dataset(file_id, result_df)

            with st.spinner("Melatih ulang model KMeans..."):
                train_kmeans_with_selected_files([file_id])
                log_model_training([file_id])

            st.success(f"File berhasil disimpan ke database dengan ID: {file_id} dan model telah diperbarui!")

    st.subheader("⚙️ Manajemen Model")
    with st.expander("Reset Model"):
        st.warning("Ini akan menghapus model lama dan melatih ulang berdasarkan seluruh data yang ada.")
        if st.checkbox("Saya yakin ingin mereset model"):
            if st.button("Reset Model (Latih ulang dari seluruh data)"):
                with st.spinner("Sedang melatih ulang model dari awal..."):
                    clear_model_training_logs()
                    train_and_save_kmeans()
                st.success("✅ Model berhasil di-reset dan dilatih ulang dari seluruh data yang ada.")
                time.sleep(3)
                st.rerun()

    with st.expander("🔁 Latih Ulang Manual (Pilih File)"):
        file_options = pd.read_sql("SELECT id, file_name FROM uploaded_files ORDER BY uploaded_at DESC", engine)
        if not file_options.empty:
            selected_ids = st.multiselect("Pilih file yang akan digunakan untuk pelatihan:",
                                          options=file_options['id'],
                                          format_func=lambda x: f"ID {x} - {file_options[file_options['id']==x]['file_name'].values[0]}")
            if st.button("Latih Model dengan File Terpilih"):
                if selected_ids:
                    with st.spinner("Melatih model dengan file terpilih..."):
                        train_kmeans_with_selected_files(selected_ids)
                        log_model_training(selected_ids)
                    st.success("✅ Model berhasil dilatih ulang dengan file yang dipilih.")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.warning("Silakan pilih minimal satu file terlebih dahulu.")

    st.subheader("🏷️ Pengaturan Label Cluster untuk Visualisasi")
    st.markdown("Label ini hanya digunakan untuk visualisasi, tidak memengaruhi data asli.")
    label_options = ["Tinggi", "Sedang", "Rendah"]
    assigned_labels = {}
    used_labels = set()
    for cluster_id in range(3):
        available_labels = [lbl for lbl in label_options if lbl not in used_labels or st.session_state.cluster_labels.get(cluster_id) == lbl]
        selected = st.selectbox(f"Label untuk Cluster {cluster_id}", options=available_labels, index=available_labels.index(st.session_state.cluster_labels.get(cluster_id)), key=f"viz_label_{cluster_id}")
        assigned_labels[cluster_id] = selected
        used_labels.add(selected)

    if st.button("Terapkan Label Visualisasi"):
        st.session_state.cluster_labels = assigned_labels
        save_cluster_labels(assigned_labels)
        st.session_state.label_applied = True
        st.success("✅ Label visualisasi cluster berhasil diperbarui dan disimpan.")

    st.markdown("---")
    st.header("📁 Daftar File yang Sudah Diupload")

    all_files = pd.read_sql("SELECT * FROM uploaded_files ORDER BY uploaded_at DESC", engine)
    if not all_files.empty:
        show_all = st.checkbox("Tampilkan semua file", value=False)
        files_to_display = all_files if show_all else all_files.head(5)

        st.markdown("""
        <style>
            .scrollable-container {
                max-height: 500px;
                overflow-y: auto;
                padding-right: 10px;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 1rem;
            }
        </style>
        """, unsafe_allow_html=True)

        with st.container():
            if show_all:
                st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)

            for index, row in files_to_display.iterrows():
                with st.expander(f"{row['file_name']} ({row['uploaded_at'][:19]})"):
                    df_preview = pd.read_sql_table(f"dataset_{row['id']}", con=engine)
                    preview_option = st.radio("Tampilkan:", ["5 Data Pertama", "Seluruh Data"], horizontal=True, key=f"preview_option_{row['id']}")
                    if preview_option == "5 Data Pertama":
                        st.dataframe(df_preview.head())
                    else:
                        st.dataframe(df_preview)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.checkbox(f"Konfirmasi hapus file ID {row['id']}"):
                            if st.button("Hapus", key=f"hapus_{row['id']}"):
                                with engine.begin() as conn:
                                    conn.execute(text("DELETE FROM uploaded_files WHERE id = :id"), {"id": row['id']})
                                st.success("✅ File berhasil dihapus.")
                                st.rerun()
                    with col2:
                        new_name = st.text_input("Ganti Nama File", value=row['file_name'], key=f"rename_{row['id']}")
                        if st.button("Simpan Nama Baru", key=f"simpan_{row['id']}"):
                            with engine.begin() as conn:
                                conn.execute(text("UPDATE uploaded_files SET file_name = :name WHERE id = :id"), {"name": new_name, "id": row['id']})
                            st.rerun()

            if show_all:
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Belum ada file yang diupload.")

    st.markdown("---")
    st.header("🧠 Riwayat Pelatihan Model")
    show_model_training_history()
