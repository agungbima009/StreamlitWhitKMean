import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import engine


# ======================================
# CSS Styling Glassmorphism
# ======================================
def set_background():
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #7F00FF, #E100FF);
            background-attachment: fixed;
            color: white;
        }
        [data-testid="stSidebar"] {
            background-color: rgba(33, 33, 33, 0.95);
            border-radius: 16px;
            padding: 16px;
        }
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.37);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            transition: all 0.3s ease-in-out;
        }
        div[data-testid="metric-container"]:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 10px 40px rgba(0,0,0,0.45);
        }
        h1, h2, h3, h4, h5, h6 {
            color: white;
        }
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 10px;
        }
        
        </style>
    """, unsafe_allow_html=True)




# ======================================
# Glassmorphism Container
# ======================================
def glassmorphism_container(title, content):
    st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.37);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        ">
        <h3 style='text-align:center'>{title}</h3>
        
    """, unsafe_allow_html=True)

    content()

    st.markdown("</div>", unsafe_allow_html=True)
    
    
def render_card(title, value, subtitle=""):
    st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.37);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            text-align: center;
            color: white;
            display: flex;
            gap: 20px;
            align-items: center;
            justify-content: center;
        ">
        <div  style="align-items: center;">{title}</div>
        <div>
            <div style="font-size:16px; opacity:0.8; text-align: left;">{subtitle}</div>
            <div style="font-size:30px;font-weight:bold;">{value}</div>
            
        </div>

        </div>
    """, unsafe_allow_html=True)



# ======================================
# Plotly Styling
# ======================================
def set_plotly_style(fig):
    fig.update_layout(
        paper_bgcolor='rgba(255,255,255,0.05)',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white'),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            zeroline=False,
            color='white'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.2)',
            zeroline=False,
            color='white'
        ),
        legend=dict(
            bgcolor='rgba(255,255,255,0.1)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1,
            font=dict(color='white'),
            orientation='h',
            yanchor='bottom',
            y=0.01,
            xanchor='left',
            x=0.01
        )
    )
    return fig


# ======================================
# Scorecard — Individual Glass Cards
# ======================================
def show_scorecard(df):
    
    jumlah_lokasi = len(df)
    total_pasar = int(df["JumlahPasar"].sum())
    rata_rata_harga = round(df["RataRataHarga"].mean(), 2)

    if not df.empty:
        max_row = df.loc[df['RataRataHargaTertinggiDiPasar'].idxmax()]
        harga_tertinggi = max_row["RataRataHargaTertinggiDiPasar"]
        nama_pasar = max_row["PasarDenganRataRataHargaTertinggi"]
        nama_lokasi = max_row["Lokasi"]
    else:
        harga_tertinggi = 0
        nama_pasar = "-"
        nama_lokasi = "-"

    
    
    # Baris 1 → Dua kolom
    col1, col2, col3 = st.columns([1, 1, 1])

    # Baris 2→ Full width
    col4 = st.columns([1])[0]


    with col1:
        render_card("""<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-geo-alt-fill" viewBox="0 0 16 16"><path d="M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10m0-7a3 3 0 1 1 0-6 3 3 0 0 1 0 6"/></svg>""", jumlah_lokasi, "Lokasi yang tersedia")

    with col2:
        render_card("""<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-shop-window" viewBox="0 0 16 16"><path d="M2.97 1.35A1 1 0 0 1 3.73 1h8.54a1 1 0 0 1 .76.35l2.609 3.044A1.5 1.5 0 0 1 16 5.37v.255a2.375 2.375 0 0 1-4.25 1.458A2.37 2.37 0 0 1 9.875 8 2.37 2.37 0 0 1 8 7.083 2.37 2.37 0 0 1 6.125 8a2.37 2.37 0 0 1-1.875-.917A2.375 2.375 0 0 1 0 5.625V5.37a1.5 1.5 0 0 1 .361-.976zm1.78 4.275a1.375 1.375 0 0 0 2.75 0 .5.5 0 0 1 1 0 1.375 1.375 0 0 0 2.75 0 .5.5 0 0 1 1 0 1.375 1.375 0 1 0 2.75 0V5.37a.5.5 0 0 0-.12-.325L12.27 2H3.73L1.12 5.045A.5.5 0 0 0 1 5.37v.255a1.375 1.375 0 0 0 2.75 0 .5.5 0 0 1 1 0M1.5 8.5A.5.5 0 0 1 2 9v6h12V9a.5.5 0 0 1 1 0v6h.5a.5.5 0 0 1 0 1H.5a.5.5 0 0 1 0-1H1V9a.5.5 0 0 1 .5-.5m2 .5a.5.5 0 0 1 .5.5V13h8V9.5a.5.5 0 0 1 1 0V13a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5a.5.5 0 0 1 .5-.5"/></svg>""", total_pasar, "Jumlah seluruh pasar")

    with col3:
        render_card(
            """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-radar" viewBox="0 0 16 16"><path d="M6.634 1.135A7 7 0 0 1 15 8a.5.5 0 0 1-1 0 6 6 0 1 0-6.5 5.98v-1.005A5 5 0 1 1 13 8a.5.5 0 0 1-1 0 4 4 0 1 0-4.5 3.969v-1.011A2.999 2.999 0 1 1 11 8a.5.5 0 0 1-1 0 2 2 0 1 0-2.5 1.936v-1.07a1 1 0 1 1 1 0V15.5a.5.5 0 0 1-1 0v-.518a7 7 0 0 1-.866-13.847"/></svg>""", 
            f"Rp {rata_rata_harga:,.2f}", 
            "Harga rata-rata Jawa Timur"
        )

    with col4:
        render_card(
            """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" class="bi bi-clipboard2-pulse-fill" viewBox="0 0 16 16"><path d="M10 .5a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5.5.5 0 0 1-.5.5.5.5 0 0 0-.5.5V2a.5.5 0 0 0 .5.5h5A.5.5 0 0 0 11 2v-.5a.5.5 0 0 0-.5-.5.5.5 0 0 1-.5-.5"/><path d="M4.085 1H3.5A1.5 1.5 0 0 0 2 2.5v12A1.5 1.5 0 0 0 3.5 16h9a1.5 1.5 0 0 0 1.5-1.5v-12A1.5 1.5 0 0 0 12.5 1h-.585q.084.236.085.5V2a1.5 1.5 0 0 1-1.5 1.5h-5A1.5 1.5 0 0 1 4 2v-.5q.001-.264.085-.5M9.98 5.356 11.372 10h.128a.5.5 0 0 1 0 1H11a.5.5 0 0 1-.479-.356l-.94-3.135-1.092 5.096a.5.5 0 0 1-.968.039L6.383 8.85l-.936 1.873A.5.5 0 0 1 5 11h-.5a.5.5 0 0 1 0-1h.191l1.362-2.724a.5.5 0 0 1 .926.08l.94 3.135 1.092-5.096a.5.5 0 0 1 .968-.039Z"/></svg>""",
            f"Rp {harga_tertinggi:,.2f}",
            f" Rata-Rata Harga Tertinggi di {nama_pasar} - {nama_lokasi}"
        )


# ======================================
# Cluster Map
# ======================================
def show_clustermap(df, label_map=None):
    glassmorphism_container("🗺️ Wilayah Dengan Cluster Tingkat Harga di Jawa Timur", lambda: render_map(df, label_map))

def render_map(df, label_map=None):
    required_columns = {"cluster", "Latitude", "Longitude", "Lokasi", "RataRataHarga"}
    if not required_columns.issubset(df.columns):
        missing_cols = required_columns - set(df.columns)
        st.error(f"❌ Kolom yang hilang: {missing_cols}")
        st.info(f"✅ Kolom yang tersedia: {list(df.columns)}")
        return

    try:
        df_map = df.copy()

        # Konversi tipe data
        df_map['cluster'] = pd.to_numeric(df_map['cluster'], errors='coerce').astype('Int64')
        df_map['Latitude'] = pd.to_numeric(df_map['Latitude'], errors='coerce')
        df_map['Longitude'] = pd.to_numeric(df_map['Longitude'], errors='coerce')
        df_map['RataRataHarga'] = pd.to_numeric(df_map['RataRataHarga'], errors='coerce')

        # Buang data yang tidak valid
        df_map = df_map.dropna(subset=['Latitude', 'Longitude', 'cluster', 'RataRataHarga'])

        if df_map.empty:
            st.error("❌ Tidak ada data valid untuk ditampilkan di peta.")
            return

        # Gunakan label dari parameter (hasil dari load_cluster_labels)
        default_labels = {0: "Tinggi", 1: "Sedang", 2: "Rendah"}
        cluster_labels = label_map if label_map is not None else st.session_state.get("cluster_labels", default_labels)

        # Mapping warna dan ukuran marker
        color_map = {"Tinggi": "#4CAF50", "Sedang": "#FFC107", "Rendah": "#F44336"}
        size_map = {"Tinggi": 20, "Sedang": 10, "Rendah": 5}

        df_map['cluster_label'] = df_map['cluster'].map(cluster_labels).fillna("Tidak Terdefinisi")
        df_map['size'] = df_map['cluster_label'].map(size_map).fillna(8)

        # Scatter Mapbox
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

        # Style Peta
        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox_center={"lat": -7.5, "lon": 112.5},
            margin={"r": 0, "t": 20, "l": 0, "b": 0},
            showlegend=True,
            legend=dict(
                title=None,
                bgcolor="rgba(255, 255, 255, 0.7)",
                bordercolor="rgba(0, 0, 0, 0.5)",
                borderwidth=1,
                font=dict(color="black", size=16),
                orientation="h",
                yanchor="bottom",
                y=0.01,
                xanchor="left",
                x=0.01
            )
        )

        st.plotly_chart(set_plotly_style(fig), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error saat membuat peta: {str(e)}")
        st.write("🔧 Debug Info:")
        st.write(f"Data shape: {df.shape}")
        st.write(f"Columns: {list(df.columns)}")
        st.dataframe(df.head(3))

# ======================================
# Top Bottom Bar Chart
# ======================================
def show_top_bottom_locations(df):
    glassmorphism_container("📊 5 Lokasi Dengan Harga Tertinggi dan Terendah", lambda: render_top_bottom(df))


def render_top_bottom(df):
    df_grouped = df.groupby("Lokasi")["RataRataHarga"].mean().reset_index()

    df_top5 = df_grouped.sort_values(by="RataRataHarga", ascending=False).head(5)
    df_bottom5 = df_grouped.sort_values(by="RataRataHarga", ascending=True).head(5)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h4 style='text-align:center;'>5 Lokasi Tertinggi</h4>", unsafe_allow_html=True)
        fig_top = px.bar(
            df_top5.sort_values("RataRataHarga"),
            x="RataRataHarga",
            y="Lokasi",
            orientation="h",
            text="RataRataHarga",
            color_discrete_sequence=["#00C9FF"]
        )
        fig_top.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(set_plotly_style(fig_top), use_container_width=True, key="top5_chart")

    with col2:
        st.markdown("<h4 style='text-align:center;'>5 Lokasi Terendah</h4>", unsafe_allow_html=True)
        fig_bot = px.bar(
            df_bottom5.sort_values("RataRataHarga"),
            x="RataRataHarga",
            y="Lokasi",
            orientation="h",
            text="RataRataHarga",
            color_discrete_sequence=["#FA5F55"]
        )
        fig_bot.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(set_plotly_style(fig_bot), use_container_width=True, key="bottom5_chart")


# ======================================
# Line Chart Price Trend
# ======================================
def show_price_trend():
    glassmorphism_container("📈 Tren Rata-Rata Harga Seluruh Kabupaten/Kota", render_trend)


def render_trend():
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'dataset_%'",
        engine
    )

    trend_data = []
    for (table_name,) in tables.itertuples(index=False):
        try:
            df = pd.read_sql_table(table_name, engine)
            file_id = int(table_name.replace("dataset_", ""))

            uploaded_at_df = pd.read_sql(
                f"SELECT uploaded_at FROM uploaded_files WHERE id={file_id}",
                engine
            )
            if uploaded_at_df.empty:
                continue

            uploaded_at = uploaded_at_df.iloc[0, 0]
            rata_rata = df["RataRataHarga"].mean()

            trend_data.append({
                "uploaded_at": uploaded_at,
                "RataRataHarga": rata_rata
            })
        except Exception as e:
            st.warning(f"Gagal membaca {table_name}: {e}")

    if not trend_data:
        st.info("Belum ada data untuk tren harga.")
        return

    df_trend = pd.DataFrame(trend_data).sort_values("uploaded_at")
    df_trend['uploaded_at'] = pd.to_datetime(df_trend['uploaded_at'])

    fig = px.line(df_trend, x="uploaded_at", y="RataRataHarga", markers=True)
    fig.update_traces(line_color="#00FFD5", marker_color="#00FFD5")

    st.plotly_chart(set_plotly_style(fig), use_container_width=True)


# ======================================
# Data Table
# ======================================
def show_data_table(df):
    glassmorphism_container("🗒️ Data Tabel", lambda: render_table(df))


def render_table(df):
    if df.empty:
        st.info("Data kosong atau belum dipilih.")
        return

    first_col = df.columns[0]
    if first_col.lower() in ["unnamed: 0", "index", "0"]:
        df = df.drop(columns=first_col)

    hide_columns_positions = [0, 6, 7, 8]
    hide_columns_positions = [idx for idx in hide_columns_positions if idx < len(df.columns)]
    hide_columns = [df.columns[idx] for idx in hide_columns_positions]
    columns_to_display = [col for col in df.columns if col not in hide_columns]

    st.dataframe(df[columns_to_display])
