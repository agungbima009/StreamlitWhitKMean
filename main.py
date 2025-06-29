import streamlit as st
import admin_dashboard

from utils.auth import login

# ===============================
# Konfigurasi Halaman
# ===============================
st.set_page_config(
    page_title="Visualisasi Clustering",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
import dashboard_user

# ===============================
# Styling CSS — Sama dengan Visualisasi.py
# ===============================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }

    .stApp header {
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }

    [data-testid="stSidebar"] {
        background-color: rgba(33, 33, 33, 0.9);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }

    .sidebar-title {
        color: white;
        font-size: 1.6rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }

    .page-indicator {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 0.7rem 1rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(8px);
        color: white;
        text-align: center;
        margin-top: 1rem;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .nav-section {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(8px);
        margin-top: 1.5rem;
        color: white;
    }

    h1, h2, h3, h4, h5, h6 {
        color: white;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }

</style>
""", unsafe_allow_html=True)


# ===============================
# Sidebar dengan Desain Modern
# ===============================
with st.sidebar:
    st.markdown('''
        <div class="sidebar-title">
            Navigation
        </div>
    ''', unsafe_allow_html=True)

    page = st.selectbox(
        "Pilih Halaman",
        [
            "User Dashboard",
            "Admin Dashboard"
        ],
        help="Pilih halaman yang ingin Anda akses"
    )

    if page == "User Dashboard":
        st.markdown("""
        <div class="page-indicator">
            📊 Mode: User Dashboard
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="page-indicator">
            ⚙️ Mode: Admin Dashboard
        </div>
        """, unsafe_allow_html=True)

   



# ===============================
# Routing halaman
# ===============================
if page == "User Dashboard":
    dashboard_user.render()

elif page == "Admin Dashboard":
    if st.session_state.get("authenticated"):
        admin_dashboard.render()
    else:
        login()
