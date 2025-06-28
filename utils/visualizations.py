import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from sqlalchemy import text
from utils.db import engine
from sklearn.metrics import silhouette_score

def show_scorecard(df):
    col1, col2, col3, col4 = st.columns(4)

    # Jumlah lokasi = banyak baris
    col1.metric("Jumlah Lokasi", len(df))

    # Jumlah total pasar dari seluruh baris
    total_pasar = int(df["JumlahPasar"].sum())
    col2.metric("Total Jumlah Pasar", total_pasar)

    # Rata-rata harga
    rata_rata_harga = round(df['RataRataHarga'].mean(), 2)
    col3.metric("Rata-rata Harga Jawa Timur", f"Rp {rata_rata_harga:,.2f}")

    # Harga pasar tertinggi
    if not df.empty:
        max_row = df.loc[df['RataRataHargaTertinggiDiPasar'].idxmax()]
        nama_pasar = max_row['PasarDenganRataRataHargaTertinggi']
        nama_lokasi = max_row['Lokasi']
        harga_tertinggi = max_row['RataRataHargaTertinggiDiPasar']

        col4.metric(
            label="Harga Tertinggi di Pasar",
            value=f"Rp {harga_tertinggi:,.2f}",
            delta=f"{nama_pasar} - {nama_lokasi}"
        )
    else:
        col4.metric("Harga Tertinggi di Pasar", "Data tidak tersedia", "")


def show_clustermap(df):
    st.subheader("🗺️ Wilayah Dengan Cluster Tingkat Harga di Jawa Timur")

    required_columns = {"cluster", "Latitude", "Longitude", "Lokasi", "RataRataHarga"}
    if not required_columns.issubset(df.columns):
        missing_cols = required_columns - set(df.columns)
        st.error(f"❌ Kolom yang hilang: {missing_cols}")
        st.info(f"✅ Kolom yang tersedia: {list(df.columns)}")
        return

    try:
        df_map = df.copy()
        df_map['cluster'] = df_map['cluster'].astype(int)
        df_map['Latitude'] = pd.to_numeric(df_map['Latitude'], errors='coerce')
        df_map['Longitude'] = pd.to_numeric(df_map['Longitude'], errors='coerce')
        df_map['RataRataHarga'] = pd.to_numeric(df_map['RataRataHarga'], errors='coerce')
        df_map = df_map.dropna(subset=['Latitude', 'Longitude', 'RataRataHarga'])

        if len(df_map) == 0:
            st.error("❌ Tidak ada data valid untuk ditampilkan")
            return

        default_labels = {0: "Tinggi", 1: "Sedang", 2: "Rendah"}
        cluster_labels = st.session_state.get("cluster_labels", default_labels)

        color_map = {"Tinggi": "#4CAF50", "Rendah": "#F44336", "Sedang": "#FFC107"}
        size_map = {"Tinggi": 20, "Sedang": 10, "Rendah": 5}

        df_map['cluster_label'] = df_map['cluster'].map(cluster_labels)
        df_map['size'] = df_map['cluster_label'].map(size_map).fillna(8)

        fig = px.scatter_mapbox(
            df_map,
            lat="Latitude",
            lon="Longitude",
            color="cluster_label",
            size="size",
            hover_name="Lokasi",
            hover_data={"RataRataHarga": True, "Latitude": False, "Longitude": False},
            zoom=7,
            height=550,
            color_discrete_map=color_map,
            size_max=30
        )

        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox_center={"lat": -7.5, "lon": 112.5},
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error saat membuat peta: {str(e)}")
        st.write("Debug info:")
        st.write(f"Data shape: {df.shape}")
        st.write(f"Columns: {list(df.columns)}")
        if len(df) > 0:
            st.write("Sample data:")
            st.dataframe(df.head(3))

def show_top_bottom_locations(df):
    st.subheader("📊 5 Lokasi dengan Harga Tertinggi dan Terendah")

    if "Lokasi" not in df.columns or "RataRataHarga" not in df.columns:
        st.error("Data tidak mengandung kolom 'Lokasi' atau 'RataRataHarga'")
        return

    df_grouped = df.groupby("Lokasi")["RataRataHarga"].mean().reset_index()
    df_top5 = df_grouped.sort_values(by="RataRataHarga", ascending=False).head(5)
    df_bottom5 = df_grouped.sort_values(by="RataRataHarga", ascending=True).head(5)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<h4 style='text-align:center;'>5 Lokasi Tertinggi</h4>", unsafe_allow_html=True)
        fig_top = px.bar(
            df_top5.sort_values("RataRataHarga"),
            x="RataRataHarga",
            y="Lokasi",
            orientation="h",
            text="RataRataHarga",
            color_discrete_sequence=["#73D2F6"]
        )
        fig_top.update_traces(texttemplate='%{text:.2f}', textposition='outside', width=0.4)
        fig_top.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        st.markdown("<h4 style='text-align:center;'>5 Lokasi Terendah</h4>", unsafe_allow_html=True)
        fig_bot = px.bar(
            df_bottom5.sort_values("RataRataHarga"),
            x="RataRataHarga",
            y="Lokasi",
            orientation="h",
            text="RataRataHarga",
            color_discrete_sequence=["#73D2F6"]
        )
        fig_bot.update_traces(texttemplate='%{text:.2f}', textposition='outside', width=0.4)
        fig_bot.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_bot, use_container_width=True)

def show_price_trend():
    st.subheader("📈 Linechart Rata-Rata Harga Seluruh Kab/Kota")
    tables = pd.read_sql("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'dataset_%'
    """, engine)

    trend_data = []
    for (table_name,) in tables.itertuples(index=False):
        try:
            df = pd.read_sql_table(table_name, engine)
            file_id = int(table_name.replace("dataset_", ""))

            uploaded_at_df = pd.read_sql(
                f"SELECT uploaded_at FROM uploaded_files WHERE id={file_id}", engine
            )

            if uploaded_at_df.empty:
                continue  # Lewati jika tidak ada info waktu upload

            uploaded_at = uploaded_at_df.iloc[0, 0]
            rata_rata = df["RataRataHarga"].mean()
            trend_data.append({
                "uploaded_at": uploaded_at,
                "RataRataHarga": rata_rata
            })
        except Exception as e:
            st.warning(f"Gagal membaca data dari {table_name}: {e}")

    if not trend_data:
        st.info("Belum ada data yang bisa ditampilkan untuk tren harga.")
        return

    df_trend = pd.DataFrame(trend_data).sort_values("uploaded_at")
    df_trend['uploaded_at'] = pd.to_datetime(df_trend['uploaded_at'])

    fig = px.line(df_trend, x="uploaded_at", y="RataRataHarga", markers=True)
    fig.update_layout(
        xaxis_title="Waktu Upload",
        yaxis_title="Rata-rata Harga",
        # title={"text": "Perkembangan Harga dari Waktu ke Waktu", "x": 0.5},
        height=450
    )
    st.plotly_chart(fig, use_container_width=True)

def show_data_table(df):
    st.subheader("🗒️ Data Tabel")

    if df.empty:
        st.info("Data kosong atau belum dipilih.")
        return

    # Deteksi jika ada kolom index seperti Unnamed: 0, hapus itu dulu
    first_col = df.columns[0]
    if first_col.lower() in ["unnamed: 0", "index", "0"]:
        df = df.drop(columns=first_col)

    # ===============================
    # ✅ Tentukan kolom yang akan di-hide
    # ===============================
    hide_columns_positions = [0, 6, 7, 8]  # Kolom ke-1,7,8,9 (posisi 0-based)

    # Pastikan posisi tidak melebihi jumlah kolom yang ada
    hide_columns_positions = [
        idx for idx in hide_columns_positions if idx < len(df.columns)
    ]

    # Dapatkan nama kolom yang ingin disembunyikan
    hide_columns = [df.columns[idx] for idx in hide_columns_positions]

    # Pilih kolom yang tidak disembunyikan
    columns_to_display = [col for col in df.columns if col not in hide_columns]

    # ===============================
    # ✅ Tampilkan dataframe dengan kolom yang sudah di-hide
    # ===============================
    st.dataframe(df[columns_to_display])