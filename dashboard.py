import streamlit as st
from supabase import create_client, Client
from scanner import scan_for_phi
import pandas as pd
import io
import zipfile
import time

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Compliance Lite", layout="wide", page_icon="🛡️")

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "batch_results" not in st.session_state:
    st.session_state.batch_results = []
if "zip_buffer" not in st.session_state:
    st.session_state.zip_buffer = None
if "audit_log" not in st.session_state:
    st.session_state.audit_log = None

# ── DATABASE ──────────────────────────────────────────────────────────────────
@st.cache_resource
def _get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# ── LOGIN SCREEN ──────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <style>
        /* ── Background ── */
        .stApp {
            background: radial-gradient(circle at center, #1e293b, #0c111c) !important;
            background-attachment: fixed !important;
        }

        /* ── Header/Footer Cleanup ── */
        [data-testid="stHeader"], [data-testid="stFooter"] { display: none !important; }

        /* ── THE LOGIN CARD ── */
        .login-card-marker { display: none; }
        [data-testid="stColumn"]:has(.login-card-marker) {
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            z-index: 9999 !important;
            width: 420px !important;
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 28px !important;
            padding: 40px !important;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5) !important;
        }

        /* ── FIX: INPUT TEXT VISIBILITY ── */
        input {
            color: #1E1E1E !important; /* Dark text for visibility */
            background-color: #FFFFFF !important; /* White background */
        }

        /* ── FIX: KILL THE BLACK BOX (Adornment) ── */
        div[data-testid="stInputAdornment"], 
        div[data-testid="stInputAdornment"] button {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* ── Sign In button ── */
        [data-testid="stColumn"]:has(.login-card-marker) .stButton > button {
            width: 100% !important;
            background: #3b82f6 !important;
            color: #ffffff !important;
            border-radius: 12px !important;
            min-height: 50px !important;
            font-weight: 700 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    login_error = st.session_state.pop("login_error", None)
    login_placeholder = st.empty()

    with login_placeholder.container():
        _, col, _ = st.columns([1, 1.4, 1])
        with col:
            st.markdown('<span class="login-card-marker"></span>', unsafe_allow_html=True)
            if login_error:
                st.error(login_error)

            st.markdown(
                '<div style="text-align:center;">'
                '<div style="font-size:44px; margin-bottom:10px;">🛡️</div>'
                '<h2 style="color:#f1f5f9; font-size:22px; font-weight:700; margin:0 0 5px 0;">Compliance Lite</h2>'
                '<p style="color:#94a3b8; font-size:14px; margin:0 0 30px 0;">Enterprise PHI Detection</p>'
                '</div>',
                unsafe_allow_html=True,
            )

            email = st.text_input("Email", placeholder="Email Address", key="login_email", label_visibility="collapsed")
            password = st.text_input("Password", placeholder="Password", key="login_password", label_visibility="collapsed", type="password")

            if st.button("Sign In →", key="login_btn"):
                try:
                    response = _get_supabase().auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.authenticated = True
                    st.session_state.user = response.user
                    st.rerun()
                except Exception as e:
                    st.session_state.login_error = "Invalid Credentials"
                    st.rerun()

            st.markdown(
                '<div style="margin-top:14px; background:rgba(255,255,255,0.04); border-radius:12px; padding:12px; font-size:12px; color:#94a3b8; text-align:center;">'
                'demo@katiegray.design | Compliance2026'
                '</div>', unsafe_allow_html=True)

# ── DASHBOARD STYLES ──────────────────────────────────────────────────────────
DASHBOARD_CSS = """
<style>
    .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a); color: #f8fafc; }
    
    /* FIX: Top Header Banner */
    .main-header {
        width: 100% !important; padding: 40px;
        background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%) !important;
        text-align: center; border-radius: 20px; margin-bottom: 2rem;
    }
    
    /* FIX: Uploader Text Visibility */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(255,255,255,0.05) !important;
        color: white !important;
    }
    
    /* FIX: Sanitize Button Contrast */
    div.stButton > button {
        background: #3b82f6 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 0.6rem 2rem !important;
        font-weight: bold !important;
    }

    /* FIX: File Uploader Instructions */
    [data-testid="stFileUploadDropzoneInstructions"] div {
        color: #ffffff !important;
    }
</style>
"""

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def show_dashboard(user_id: str, user_email: str):
    def get_historical_audits(uid: str):
        try:
            res = _get_supabase().table("scan_history").select("*").eq("user_id", uid).order("created_at", desc=True).limit(10).execute()
            return pd.DataFrame(res.data) if res.data else None
        except: return None

    def save_to_cloud(filename, risk, count):
        try:
            _get_supabase().table("scan_history").insert({"filename": filename, "risk_status": risk, "phi_count": int(count), "user_id": user_id}).execute()
        except: pass

    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### Admin Portal")
        st.write(f"**Operator:** Katie Gray")
        st.write(f"**Account:** {user_email}")
        if st.button("Sign Out"):
            _get_supabase().auth.sign_out()
            st.session_state.authenticated = False
            st.rerun()

    st.markdown('<div class="main-header"><h1 style="color:white; margin:0;">🛡️ Compliance Lite</h1><p style="color:white; opacity:0.8;">Enterprise PHI Detection</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Batch Processing")
        uploaded_files = st.file_uploader("Upload Files", accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")
        
        if st.button("🛡️ Sanitize & Log Batch"):
            if uploaded_files:
                zip_mem = io.BytesIO()
                batch_data = []
                with zipfile.ZipFile(zip_mem, "w") as zf:
                    for f in uploaded_files:
                        content = f.read().decode("utf-8", errors="replace")
                        results = scan_for_phi(content)
                        risk = "HIGH_RISK" if results["phi_found"] else "SAFE"
                        count = len(results.get("phones", [])) + len(results.get("emails", []))
                        save_to_cloud(f.name, risk, count)
                        zf.writestr(f"CLEAN_{f.name}", results.get("sanitized_text", content))
                        batch_data.append({"File": f.name, "Risk": risk, "PHI": count, "Preview": results.get("sanitized_text", content)[:300]})
                st.session_state.batch_results = batch_data
                st.session_state.zip_buffer = zip_mem.getvalue()
                st.session_state.audit_log = get_historical_audits(user_id)
                st.rerun()

    with col2:
        if st.session_state.batch_results:
            st.markdown("### Results")
            st.download_button("📥 Download Sanitized ZIP", data=st.session_state.zip_buffer, file_name="Sanitized_Docs.zip")
            for item in st.session_state.batch_results:
                with st.expander(f"{item['File']} - {item['Risk']}"):
                    st.code(item["Preview"])

    st.divider()
    st.markdown("### Recent Activity Audit Log")
    if st.session_state.audit_log is None:
        st.session_state.audit_log = get_historical_audits(user_id)
    
    if st.session_state.audit_log is not None:
        st.dataframe(st.session_state.audit_log, use_container_width=True, hide_index=True)

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if st.session_state.authenticated and st.session_state.user:
    show_dashboard(st.session_state.user.id, st.session_state.user.email)
else:
    show_login()