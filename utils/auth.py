import streamlit as st
import bcrypt
import json
import os
import re

CONFIG_PATH = "config.json"

# Muat file konfigurasi
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"username": "admin", "password": "", "security_question": "", "security_answer": ""}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

# Simpan konfigurasi
def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

# Validasi kekuatan password
def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[^\w\s]", password):
        return False
    return True

# Login form
import streamlit as st
import bcrypt
import json

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def save_config(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)


# ====================
# Fungsi Login Utama
# ====================
def login():
    config = load_config()

    # Inisialisasi session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'show_reset' not in st.session_state:
        st.session_state.show_reset = False
    if 'login_failed' not in st.session_state:
        st.session_state.login_failed = False

    if not st.session_state.authenticated:
        st.subheader("🔐 Login Admin")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if (
                username == config.get("username")
                and bcrypt.checkpw(password.encode(), config.get("password").encode())
            ):
                st.session_state.authenticated = True
                st.session_state.login_failed = False
                st.session_state.show_reset = False
                st.success("✅ Login berhasil!")
                st.rerun()
            else:
                st.session_state.login_failed = True
                st.error("❌ Username atau password salah.")

        # ========================
        # 🔐 Bagian Reset Password
        # ========================
        if st.session_state.login_failed and not st.session_state.show_reset:
            if st.button("Lupa Password"):
                st.session_state.show_reset = True

        if st.session_state.show_reset:
            st.info("🔐 Jawab pertanyaan rahasia untuk reset password.")

            question = config.get("security_question", "Pertanyaan tidak tersedia")
            answer = st.text_input(f"{question}")
            new_pass = st.text_input("Password Baru", type="password")

            if st.button("Ganti Password"):
                stored_hashed_answer = config.get("security_answer")

                # Validasi apakah security_answer ada
                if not stored_hashed_answer:
                    st.error("⚠️ Pertanyaan keamanan belum diset pada konfigurasi.")
                else:
                    if bcrypt.checkpw(answer.encode(), stored_hashed_answer.encode()):
                        if len(new_pass) < 8:
                            st.warning("⚠️ Password harus minimal 8 karakter.")
                            return

                        # Hash password baru
                        new_hash = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()

                        config["password"] = new_hash
                        save_config(config)

                        st.success("✅ Password berhasil diganti! Silakan login kembali.")
                        st.session_state.show_reset = False
                        st.session_state.login_failed = False
                    else:
                        st.error("❌ Jawaban pertanyaan keamanan salah.")

        return False

    else:
        return True


# Form reset password via pertanyaan rahasia
def show_password_reset_form():
    config = load_config()
    st.subheader("🔐 Reset Password")

    pertanyaan = config.get("security_question", "Pertanyaan tidak tersedia")
    jawaban_input = st.text_input(pertanyaan)
    new_pass = st.text_input("Password Baru", type="password")

    if st.button("Ganti Password"):
        stored_hashed_answer = config.get("security_answer", "")

        if bcrypt.checkpw(jawaban_input.strip().encode(), stored_hashed_answer.encode()):
            if not is_strong_password(new_pass):
                st.warning("⚠️ Password harus minimal 8 karakter, mengandung huruf besar, huruf kecil, angka, dan simbol.")
                return

            # Simpan password baru dengan hashing
            config["password"] = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
            save_config(config)

            st.success("✅ Password berhasil diubah! Silakan login kembali.")

            # Reset flag session
            st.session_state.show_reset = False
            st.session_state.show_reset_button = False

        else:
            st.error("❌ Jawaban pertanyaan keamanan salah.")

# Logout
def logout():
    with st.sidebar:
        if st.button("🚪 Logout"):
            st.session_state.confirm_logout = True

    # Tampilkan dialog konfirmasi jika diklik
    if st.session_state.get("confirm_logout", False):
        with st.sidebar:
            st.warning("Apakah Anda yakin ingin logout?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Ya, Logout"):
                    st.session_state.clear()
                    st.rerun()
            with col2:
                if st.button("❌ Batal"):
                    st.session_state.confirm_logout = False