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
        .stApp { background: radial-gradient(circle at center, #1e293b, #0c111c) !important; background-attachment: fixed !important; }
        [data-testid="stHeader"], [data-testid="stFooter"] { display: none !important; }

        /* THE CARD */
        .login-card-marker { display: none; }
        [data-testid="stColumn"]:has(.login-card-marker) {
            position: fixed !important; top: 50% !important; left: 50% !important;
            transform: translate(-50%, -50%) !important; z-index: 9999 !important;
            width: 420px !important; background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(20px) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 28px !important; padding: 40px !important;
        }

        /* FIX: INPUT TEXT & KILL BLACK BOX */
        input { color: #1E1E1E !important; background-color: #FFFFFF !important; }
        div[data-testid="stInputAdornment"], div[data-testid="stInputAdornment"] button {
            background-color: transparent !important; border: none !important; box-shadow: none !important;
        }

        .stButton > button { width: 100% !important; background: #3b82f6 !important; color: white !important; border-radius: 12px !important; min-height: 50px !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

    login_error = st.session_state.pop("login_error", None)
    login_placeholder = st.empty()

    with login_placeholder.container():
        _, col, _ = st.columns([1, 1.4, 1])
        with col:
            st.markdown('<span class="login-card-marker"></span>', unsafe_allow_html=True)
            if login_error: st.error(login_error)

            st.markdown('<div style="text-align:center;"><div style="font-size:44px; margin-bottom:10px;">🛡️</div><h2 style="color:#f1f5f9; font-size:22px; font-weight:700; margin:0 0 5px 0;">Compliance Lite</h2><p style="color:#94a3b8; font-size:14px; margin:0 0 5px 0;">Enterprise PHI Detection</p><p style="color:#7dd3fc; font-size:13px; font-weight:600; margin:0 0 30px 0;">ENTER DEMO CREDENTIALS BELOW TO SIGN IN</p></div>', unsafe_allow_html=True)

            email = st.text_input("Email", placeholder="Email Address", key="login_email", label_visibility="collapsed")
            password = st.text_input("Password", placeholder="Password", key="login_password", label_visibility="collapsed", type="password")

            if st.button("Sign In →", key="login_btn"):
                try:
                    response = _get_supabase().auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.authenticated = True
                    st.session_state.user = response.user
                    st.rerun()
                except:
                    st.session_state.login_error = "Invalid Credentials"
                    st.rerun()

            st.markdown('<div style="margin-top:14px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:12px 16px; font-size:12px; color:#94a3b8; text-align:center;"><strong style="color:#cbd5e1;">demo@katiegray.design</strong><br><strong style="color:#cbd5e1;">Compliance2026</strong></div>', unsafe_allow_html=True)

# ── DASHBOARD STYLES ──────────────────────────────────────────────────────────
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

    /* FIX: BROWSE FILES BUTTON VISIBILITY */
    [data-testid="stFileUploadDropzoneInstructions"] div { color: #1E1E1E !important; }
    button[data-testid="stBaseButton-secondary"] { border: 1px solid #3b82f6 !important; }

    /* Red Buttons for Dashboard */
    div:not([data-testid="stSidebar"]) .stButton > button {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
        color: white !important; border-radius: 16px !important; font-weight: 700 !important;
    }
</style>
"""

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def show_dashboard(user_id: str, user_email: str):
    def get_historical_audits(uid: str):
        try:
            response = _get_supabase().table("scan_history").select("*").eq("user_id", uid).order("created_at", desc=True).limit(15).execute()
            return pd.DataFrame(response.data) if response.data else None
        except: return None

    def save_to_cloud(filename, risk, count):
        try:
            _get_supabase().table("scan_history").insert({"filename": filename, "risk_status": risk, "phi_count": int(count), "user_id": user_id}).execute()
        except: pass

    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
    if st.session_state.audit_log is None:
        st.session_state.audit_log = get_historical_audits(user_id)

    with st.sidebar:
        st.markdown("## Admin Portal")
        st.markdown(f'<p style="font-size:0.7rem; text-transform:uppercase; color:#64748b; margin-top:14px;">Operator</p><p style="font-size:0.95rem; font-weight:600; color:#f1f5f9;">Katie Gray</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:0.7rem; text-transform:uppercase; color:#64748b; margin-top:14px;">Account</p><p style="font-size:0.95rem; font-weight:600; color:#f1f5f9;">{user_email}</p>', unsafe_allow_html=True)
        if st.button("Sign Out"):
            _get_supabase().auth.sign_out()
            st.session_state.authenticated = False; st.rerun()

    st.markdown('<div class="main-header"><h1>🛡️ Compliance Lite</h1><p>Enterprise PHI Detection</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
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
            st.download_button("📥 Download Sanitized ZIP", data=st.session_state.zip_buffer, file_name="Sanitized_Docs.zip")
            for item in st.session_state.batch_results:
                with st.expander(f"{item['File']} - {item['Risk']}"): st.code(item["Preview"])

    st.divider()
    if st.session_state.audit_log is not None:
        st.dataframe(st.session_state.audit_log, use_container_width=True, hide_index=True)

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if st.session_state.authenticated and st.session_state.user:
    show_dashboard(st.session_state.user.id, st.session_state.user.email)
else:
    show_login()