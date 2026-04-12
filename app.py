import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"

st.set_page_config(page_title="KerjaIN.ai", layout="wide")

if "role" not in st.session_state: st.session_state.role = "jobseeker"
if "cv_text" not in st.session_state: st.session_state.cv_text = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "user_name" not in st.session_state: st.session_state.user_name = ""

# Sidebar - Sistem Login
st.sidebar.title("Portal Akses")
if st.session_state.role == "jobseeker":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Login Khusus HR")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        try:
            with open("hr_users.json", "r") as f:
                hr_db = json.load(f)
            
            if username in hr_db and hr_db[username].get("password") == password:

                if hr_db[username].get("role") == "hr":
                    st.session_state.role = "hr"
                    st.session_state.user_name = hr_db[username].get("name", username)
                    st.session_state.chat_history = []
                    st.session_state.cv_text = ""
                    st.rerun()
                else:
                    st.sidebar.error("Akun ini tidak memiliki akses HR.")
            else:
                st.sidebar.error("Username atau Password tidak valid.")
        except FileNotFoundError:
            st.sidebar.error("Database sistem HR tidak ditemukan.")
else:
    st.sidebar.success("Sesi Aktif")
    st.sidebar.info(f"Login sebagai:\n{st.session_state.user_name}")
    if st.sidebar.button("Logout"):
        st.session_state.role = "jobseeker"
        st.session_state.user_name = ""
        st.session_state.chat_history = []
        st.session_state.cv_text = ""
        st.rerun()

# Header Utama
if st.session_state.role == "jobseeker":
    st.title("KerjaIN.ai")
    st.subheader("Partner AI Pencarian Kerja Anda")
else:
    st.title("Dashboard Recruiter KerjaIN.ai")
    st.subheader(f"Selamat datang, {st.session_state.user_name}!")

# Modul Upload CV
with st.expander("Modul Ekstraksi Dokumen (CV/Resume)"):
    uploaded_file = st.file_uploader("Unggah dokumen dalam format PDF, DOCX, atau JPG", type=["pdf", "docx", "jpg", "jpeg", "png"])
    if uploaded_file and st.button("Proses Dokumen"):
        with st.spinner("Mengekstrak teks dari dokumen..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            res = requests.post(f"{API_URL}/upload-cv", files=files)
            
            if res.status_code == 200:
                st.session_state.cv_text = res.json()["cv_text"]
                st.success("Dokumen berhasil diproses. Sistem siap memberikan konsultasi.")
            else:
                st.error("Gagal memproses dokumen.")

# Modul Chat
st.markdown("---")
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Ketik pertanyaan atau perintah Anda di sini...")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.write(user_input)
    
    with st.spinner("Sistem sedang menganalisis..."):
        payload = {
            "message": user_input,
            "cv_text": st.session_state.cv_text,
            "role": st.session_state.role
        }
        res = requests.post(f"{API_URL}/chat", json=payload)
        
        if res.status_code == 200:
            answer = res.json()["reply"]
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"): st.write(answer)
        else:
            st.error("Gagal terhubung ke server utama.")