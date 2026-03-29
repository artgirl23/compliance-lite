import streamlit as st
import zipfile
import io
from supabase import create_client, Client
from scanner import scan_for_phi

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Compliance Lite",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ── DATABASE ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── GLOBAL CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .stApp { background-color: #0f172a !important; color: #f8fafc !important; }
  [data-testid="stHeader"] { background: transparent !important; }
  [data-testid="stDecoration"] { display: none !important; }

  /* FIX: The "Blue Blob" Eye Icon */
  button[data-testid="stPasswordInputVisibilityToggle"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }
  button[data-testid="stPasswordInputVisibilityToggle"] svg {
    fill: none !important;
    stroke: #3b82f6 !important;
    color: #3b82f6 !important;
  }

  /* FIX: LIGHT GRAY TOGGLE ARROW */
  [data-testid="collapsedControl"] svg {
    fill: #d1d5db !important;
    color: #d1d5db !important;
  }

  .main-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #3b82f6 100%);
    border-radius: 24px;
    padding: 40px;
    margin-bottom: 20px;
    text-align: center;
  }
  
  .login-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    width: 100%;
  }
</style>
""", unsafe_allow_html=True)

# ── LOGIN ──────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<h1>🛡️ Compliance Lite</h1><p>Enterprise PHI Detection</p>', unsafe_allow_html=True)

    email = st.text_input("Email", value="demo@katiegray.design")
    password = st.text_input("Password", type="password", value="Compliance2026")

    if st.button("Sign In →", use_container_width=True):
        try:
            response = get_supabase().auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def show_dashboard():
    with st.sidebar:
        st.markdown("### Admin Portal")
        st.write("Operator: Katie Gray")
        if st.button("Sign Out", type="primary"):
            st.session_state.authenticated = False
            st.rerun()

    st.markdown('<div class="main-banner"><h1>Compliance Lite</h1><p>Secure PHI Auditing</p></div>', unsafe_allow_html=True)
    
    files = st.file_uploader("Upload", accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")

    if st.button("🛡️ Sanitize Batch", type="primary"):
        if files:
            st.success(f"Processed {len(files)} files.")
        else:
            st.warning("Upload files first.")

# ── ROUTER ─────────────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_dashboard()
else:
    show_login()