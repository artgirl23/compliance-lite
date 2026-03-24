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
    # UPDATED FOR STREAMLIT CLOUD SECRETS
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
            transition: none !important;
        }

        /* ── Kill Streamlit's default top padding ── */
        [data-testid="stAppViewContainer"] > .main { padding: 0 !important; }
        [data-testid="stHeader"],
        [data-testid="stFooter"],
        [data-testid="stSidebar"] { display: none !important; }

        /* ── No scroll ── */
        html, body { overflow: hidden !important; }

        /* ── Strip all wrapper backgrounds / borders ── */
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .main, .stMain,
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        [data-testid="stColumn"],
        .stMarkdownContainer, .element-container, .block-container {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            animation: none !important;
        }

        /* ── THE PIN: card escapes Streamlit's layout and sits dead-center ── */
        .login-card-marker { display: none; }
        [data-testid="stColumn"]:has(.login-card-marker) {
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            z-index: 9999 !important;
            width: 420px !important;
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(20px) saturate(160%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 28px !important;
            padding: 40px !important;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5) !important;
        }

        /* ── All elements inside the card: full-width, consistent ── */
        [data-testid="stColumn"]:has(.login-card-marker) .stTextInput,
        [data-testid="stColumn"]:has(.login-card-marker) .stButton,
        [data-testid="stColumn"]:has(.login-card-marker) .stAlert,
        [data-testid="stColumn"]:has(.login-card-marker) .stMarkdownContainer {
            width: 100% !important;
        }

        /* ── Inputs ── */
        [data-testid="stColumn"]:has(.login-card-marker) div[data-baseweb="input"] {
            background-color: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 12px !important;
            min-height: 48px !important;
            margin-bottom: 14px !important;
        }
        [data-testid="stColumn"]:has(.login-card-marker) div[data-baseweb="input"]:focus-within {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
        }
        [data-testid="stColumn"]:has(.login-card-marker) input {
            color: #ffffff !important;
            font-size: 15px !important;
            background-color: transparent !important;
            caret-color: #ffffff !important;
            min-height: 48px !important;
        }
        [data-testid="stColumn"]:has(.login-card-marker) label { display: none !important; }

        /* ── Sign In button: full-width blue ── */
        [data-testid="stColumn"]:has(.login-card-marker) .stButton > button {
            width: 100% !important;
            background: #3b82f6 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            min-height: 50px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            margin-top: 6px !important;
            transition: background 0.2s ease, transform 0.2s ease !important;
        }
        [data-testid="stColumn"]:has(.login-card-marker) .stButton > button:hover {
            background: #2563eb !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4) !important;
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
                '<h2 style="color:#f1f5f9; font-size:22px; font-weight:700; margin:0 0 5px 0;">'
                'Compliance Lite</h2>'
                '<p style="color:#94a3b8; font-size:14px; margin:0 0 5px 0;">'
                'Enterprise PHI Detection</p>'
                '<p style="color:#7dd3fc; font-size:12px; font-style:italic; margin:0 0 30px 0;">'
                'Demo Access: Use credentials below</p>'
                '</div>',
                unsafe_allow_html=True,
            )

            email = st.text_input("Email", placeholder="Email Address", key="login_email", label_visibility="collapsed")
            password = st.text_input("Password", placeholder="Password", key="login_password", label_visibility="collapsed", type="password")

            if st.button("Sign In →", key="login_btn"):
                if not email or not password:
                    st.session_state.login_error = "Please enter both email and password."
                    st.rerun()
                else:
                    try:
                        response = _get_supabase().auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.authenticated = True
                        st.session_state.user = response.user
                        login_placeholder.empty()
                        st.rerun()
                    except Exception as e:
                        st.session_state.login_error = str(e)
                        st.rerun()

            st.markdown(
                '<div style="margin-top:14px; background:rgba(255,255,255,0.04);'
                ' border:1px solid rgba(255,255,255,0.08); border-radius:12px;'
                ' padding:12px 16px; font-size:12px; color:#94a3b8;'
                ' line-height:1.9; text-align:center;">'
                '<strong style="color:#cbd5e1;">demo@katiegray.design</strong><br>'
                '<strong style="color:#cbd5e1;">Compliance2026</strong>'
                '</div>',
                unsafe_allow_html=True,
            )

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
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    .sidebar-label { font-size: 0.7rem; text-transform: uppercase; color: #64748b !important; margin-top: 14px; }
    .sidebar-value { font-size: 0.95rem; font-weight: 600; color: #f1f5f9 !important; }
    
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

    def _clear_batch():
        st.session_state.batch_results = []; st.session_state.zip_buffer = None; st.session_state.uploader_key += 1

    def _sign_out():
        _get_supabase().auth.sign_out()
        st.session_state.authenticated = False; st.session_state.user = None; st.rerun()

    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
    if st.session_state.audit_log is None:
        st.session_state.audit_log = get_historical_audits(user_id)

    with st.sidebar:
        st.markdown("## Admin Portal")
        st.markdown(f'<p class="sidebar-label">Operator</p><p class="sidebar-value">Katie Gray</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="sidebar-label">Account</p><p class="sidebar-value">{user_email}</p>', unsafe_allow_html=True)
        if st.button("Sign Out"): _sign_out()

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