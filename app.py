import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"

st.set_page_config(page_title="KerjaIN.ai", layout="wide")

# --- Inisialisasi State ---
if "role" not in st.session_state: st.session_state.role = "jobseeker"
if "cv_text" not in st.session_state: st.session_state.cv_text = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "last_processed_file" not in st.session_state: st.session_state.last_processed_file = ""

# --- Sidebar: Sistem Login & Navigasi ---
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
    
    st.sidebar.markdown("---")
    hr_menu = st.sidebar.radio("Menu HR:", ["Chatbot AI", "Evaluator CV"])
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Logout"):
        st.session_state.role = "jobseeker"
        st.session_state.user_name = ""
        st.session_state.chat_history = []
        st.session_state.cv_text = ""
        st.rerun()

def process_uploaded_cv(file_obj):
    files = {"file": (file_obj.name, file_obj.getvalue())}
    res = requests.post(f"{API_URL}/upload-cv", files=files)
    if res.status_code == 200:
        return res.json()["cv_text"]
    return None

# PAGE 1: MODE JOBSEEKER ATAU HR CHATBOT
if st.session_state.role == "jobseeker" or (st.session_state.role == "hr" and hr_menu == "Chatbot AI"):
    st.title("KerjaIN.ai")
    st.subheader("Partner AI Pencarian Kerja" if st.session_state.role == "jobseeker" else "Dashboard Chat HR")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    st.markdown("---")
    uploaded_file = st.file_uploader("Sertakan dokumen (CV/Resume) bersama pesan Anda (Opsional)", type=["pdf", "docx", "jpg", "jpeg", "png"])
    
    if st.session_state.cv_text:
        st.success("Terdapat CV yang sedang aktif di dalam memori AI.")

    user_input = st.chat_input("Ketik pesan atau pertanyaan di sini...")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"): 
            st.write(user_input)
        
        with st.spinner("Sistem sedang menganalisis..."):
            if uploaded_file and uploaded_file.name != st.session_state.last_processed_file:
                st.toast("Mengekstrak file dokumen...")
                extracted_text = process_uploaded_cv(uploaded_file)
                if extracted_text:
                    st.session_state.cv_text = extracted_text
                    st.session_state.last_processed_file = uploaded_file.name
                else:
                    st.error("Gagal membaca dokumen, chat dilanjutkan tanpa dokumen.")
            
            payload = {
                "message": user_input,
                "cv_text": st.session_state.cv_text,
                "role": st.session_state.role
            }
            res = requests.post(f"{API_URL}/chat", json=payload)
            
            if res.status_code == 200:
                answer = res.json()["reply"]
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
            else:
                st.error("Gagal terhubung ke server utama.")

# PAGE 2: MODE HR EVALUATOR CV
elif st.session_state.role == "hr" and hr_menu == "Evaluator CV (Batch)":
    st.title("Evaluator CV Otomatis")
    st.markdown("Fitur ini memungkinkan Anda menilai banyak kandidat sekaligus berdasarkan kriteria spesifik.")

    with st.form("evaluator_form", border=True):
        col_left, col_right = st.columns(2)
        
        with col_right:
            st.subheader("Area Unggah Dokumen")
            st.caption("Anda dapat mengunggah beberapa file CV sekaligus.")
            batch_files = st.file_uploader(
                "Unggah CV Kandidat", 
                type=["pdf", "docx", "jpg", "png"], 
                accept_multiple_files=True,
                label_visibility="collapsed"
            )

        with col_left:
            st.subheader("Kriteria Pekerjaan")
            st.caption("Tentukan syarat wajib yang harus dimiliki kandidat.")
            criteria_input = st.text_area(
                "Kriteria Input", 
                placeholder="Contoh: \n- Minimal S1 Teknik Informatika\n- Menguasai Python dan Docker\n- Pengalaman kerja minimal 2 tahun", 
                height=150,
                label_visibility="collapsed"
            )
        st.markdown("---")
        submit_eval = st.form_submit_button("Analyze", type="primary", use_container_width=True)

    if submit_eval:
        if not criteria_input:
            st.warning("Harap isi kriteria pekerjaan terlebih dahulu di sebelah kiri.")
        elif not batch_files:
            st.warning("Harap unggah minimal 1 CV kandidat di sebelah kanan.")
        else:
            for file in batch_files:
                with st.expander(f"Hasil Evaluasi: {file.name}", expanded=True):
                    with st.spinner(f"Membaca {file.name}..."):
                        cv_text = process_uploaded_cv(file)
                        
                    if cv_text:
                        with st.spinner("AI sedang mencocokkan profil dengan kriteria..."):
                            payload = {
                                "criteria": criteria_input,
                                "cv_text": cv_text
                            }
                            res = requests.post(f"{API_URL}/evaluate-cvs", json=payload)
                            
                            if res.status_code == 200:
                                st.write(res.json()["evaluation"])
                            else:
                                st.error("Gagal melakukan evaluasi dari server.")
                    else:
                        st.error("Gagal mengekstrak teks dari file ini.")