import streamlit as st
import admin_dashboard
import dashboard_user
from utils.auth import login

st.set_page_config(page_title="Visualisasi Clustering", layout="wide")

page = st.sidebar.selectbox("Pilih Halaman", [
    "User Dashboard",
    "Admin Dashboard"
])

if page == "User Dashboard":
    dashboard_user.render()
elif page == "Admin Dashboard":
    if st.session_state.get("authenticated"):
        admin_dashboard.render()
    else:
        login()
