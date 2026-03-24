import streamlit as st
from supabase import create_client, Client
from scanner import scan_for_phi
import pandas as pd
import io
import zipfile

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Compliance Lite", layout="wide", page_icon="🛡️")

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ── DATABASE ──────────────────────────────────────────────────────────────────
@st.cache_resource
def _get_supabase() -> Client:
    # Uses your existing Secrets in Streamlit Cloud
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── STYLES (The Version You Liked) ────────────────────────────────────────────
DASHBOARD_CSS = """
<style>
    .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a); background-attachment: fixed; color: #f8fafc; }
    [data-testid="stHeader"] { display: none !important; }
    
    .main-header {
        width: 100% !important; margin: 0 0 2rem 0 !important; padding: 44px 0;
        background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%) !important;
        text-align: center; border-radius: 30px;
    }
    .main-header h1 { font-size: 2.4rem; font-weight: 800; color: #ffffff !important; }

    /* Fix: Keep the Browse Files button readable */
    [data-testid="stFileUploadDropzoneInstructions"] div { color: #1E1E1E !important; }

    /* Fix: Kill the Black Box (Adornment) */
    div[data-testid="stInputAdornment"] { display: none !important; }

    /* Red Buttons for Dashboard */
    div:not([data-testid="stSidebar"]) .stButton > button {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
        color: white !important; border-radius: 16px !important; font-weight: 700 !important;
    }
</style>
"""

# ── LOGIN SCREEN ──────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <style>
        .login-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("## 🛡️ Compliance Lite")
        st.markdown("<p style='color:#7dd3fc;'>ENTER DEMO CREDENTIALS BELOW</p>", unsafe_allow_html=True)
        
        email = st.text_input("Email", placeholder="demo@katiegray.design")
        password = st.text_input("Password", type="password", placeholder="Compliance2026")
        
        if st.button("Sign In →"):
            try:
                res = _get_supabase().auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.authenticated = True
                st.session_state.user = res.user
                st.rerun()
            except:
                st.error("Invalid Login")
        
        st.markdown("<small style='color:#94a3b8;'>demo@katiegray.design | Compliance2026</small></div>", unsafe_allow_html=True)

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def show_dashboard(user_email):
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("## Admin Portal")
        st.write(f"**Operator:** Katie Gray")
        st.write(f"**Account:** {user_email}")
        if st.button("Sign Out"):
            st.session_state.authenticated = False
            st.rerun()

    st.markdown('<div class="main-header"><h1>🛡️ Compliance Lite</h1><p>Enterprise PHI Detection</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Batch Processing")
        uploaded_files = st.file_uploader("Upload Files", accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")
        if st.button("🛡️ Sanitize & Log Batch"):
            if uploaded_files:
                st.success("Files processing...") # Placeholder for logic

    with col2:
        st.subheader("Audit Log")
        st.info("Upload files to see results here.")

# ── MAIN LOGIC ────────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_dashboard(st.session_state.user.email)
else:
    show_login()