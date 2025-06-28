import streamlit as st
import pandas as pd
import time
import os
import pickle
from utils.db import save_file_metadata, save_dataset, engine
from utils.preprocessing import preprocess, preprocess_initial
from utils.train_kmeans import train_and_save_kmeans, train_kmeans_with_selected_files
from sqlalchemy import text
import utils.auth as auth



MODELS_DIR = "models"
DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

# Load KMeans model
kmeans_model_path = os.path.join(MODELS_DIR, "kmeans_model.pkl")
if os.path.exists(kmeans_model_path):
    kmeans_model = pickle.load(open(kmeans_model_path, "rb"))
else:
    kmeans_model = None


    
def render():
    # ✅ Inisialisasi session state yang diperlukan
    if "cluster_labels" not in st.session_state:
        st.session_state.cluster_labels = {0: "Tinggi", 1: "Sedang", 2: "Rendah"}
    if "label_applied" not in st.session_state:
        st.session_state.label_applied = False

    if not st.session_state.get("authenticated"):
        st.warning("Silakan login terlebih dahulu.")
        return

    auth.logout()

    st.title("Admin Panel - Upload Data")
    # ===================
    # Upload Data Baru
    # ===================
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

        # Preview clustering untuk admin (tanpa cluster_label disimpan)
        preview_df = result_df.copy()

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
        st.dataframe(preview_df)

        if st.button("Konfirmasi dan Simpan ke Database"):
            file_id = save_file_metadata(uploaded_file.name)
            save_dataset(file_id, result_df)  # result_df tanpa cluster_label

            with st.spinner("Melatih ulang model KMeans..."):
                train_and_save_kmeans()
            st.success(f"File berhasil disimpan ke database dengan ID: {file_id} dan model telah diperbarui!")

    # ===================
    # Reset Model Button
    # ===================
    st.subheader("⚙️ Manajemen Model")
    with st.expander("Reset Model"):
        st.warning("Ini akan menghapus model lama dan melatih ulang berdasarkan seluruh data yang ada.")
        if st.checkbox("Saya yakin ingin mereset model"):
            if st.button("Reset Model (Latih ulang dari seluruh data)"):
                with st.spinner("Sedang melatih ulang model dari awal..."):
                    train_and_save_kmeans()
                    st.success("✅ Model berhasil di-reset dan dilatih ulang dari seluruh data yang ada.")
                    time.sleep(3)
                st.rerun()

    # ===================
    # Manual Train Model dengan Pilihan File
    # ===================
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
                        st.success("✅ Model berhasil dilatih ulang dengan file yang dipilih.")
                        time.sleep(3)
                    st.rerun()
                else:
                    st.warning("Silakan pilih minimal satu file terlebih dahulu.")

    # ===================
    # Cluster Labeling Setting (Untuk Visualization)
    # ===================
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
        st.session_state.label_applied = True
        st.success("✅ Label visualisasi cluster berhasil diperbarui.")


    # ===================
    # Riwayat File Upload
    # ===================
    st.markdown("---")
    st.header("📁 Daftar File yang Sudah Diupload")

    files = pd.read_sql("SELECT * FROM uploaded_files ORDER BY uploaded_at DESC", engine)
    if not files.empty:
        for index, row in files.iterrows():
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
                        