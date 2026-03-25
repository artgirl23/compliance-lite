import streamlit as st
from supabase import create_client, Client

# ── 1. PAGE SETUP ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Compliance Lite", layout="centered", page_icon="🛡️")

# ── 2. SESSION STATE ──────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ── 3. DATABASE ───────────────────────────────────────────────────────────────
@st.cache_resource
def _get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── 4. STYLES (Restored to Clean V1 Vibe) ─────────────────────────────────────
st.markdown("""
<style>
    /* Dark Background */
    .stApp { background-color: #0f172a !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { display: none !important; }

    /* The Login Card Structure */
    .login-container {
        background-color: #1e293b;
        padding: 40px;
        border-radius: 24px;
        border: 1px solid #334155;
        text-align: center;
        margin-top: 50px;
    }

    /* The Blue Header (Dashboard) */
    .main-header {
        background: #3b82f6 !important;
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        color: white !important;
    }

    /* Standardized Buttons */
    div:not([data-testid="stSidebar"]) button {
        background-color: #3b82f6 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 0.6rem 2rem !important;
    }
    
    /* Logout Button stays Red */
    [data-testid="stSidebar"] button {
        background-color: #ef4444 !important;
        color: white !important;
    }

    /* Sidebar Fix */
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
</style>
""", unsafe_allow_html=True)

# ── 5. LOGIN SCREEN ───────────────────────────────────────────────────────────
def show_login():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.write("🛡️ # Compliance Lite")
    st.write("Enterprise PHI Detection")
    
    email = st.text_input("Email", value="demo@katiegray.design")
    password = st.text_input("Password", type="password", value="Compliance2026")
    
    if st.button("Sign In →"):
        try:
            _get_supabase().auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.authenticated = True
            st.rerun()
        except:
            st.error("Invalid Credentials")
    
    st.markdown("<br><small style='color:#94a3b8;'>demo@katiegray.design | Compliance2026</small>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── 6. DASHBOARD ──────────────────────────────────────────────────────────────
def show_dashboard():
    with st.sidebar:
        st.write("### Admin Portal")
        st.write("**Operator:** Katie Gray")
        if st.button("Sign Out"):
            st.session_state.authenticated = False
            st.rerun()

    st.markdown('<div class="main-header"><h1>🛡️ Compliance Lite</h1><p>Enterprise PHI Detection</p></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Batch Processing")
        st.file_uploader("Upload Files", accept_multiple_files=True)
        st.button("🛡️ Sanitize & Log Batch")

    with c2:
        st.subheader("Recent Activity Audit Log")
        st.write("Ready for scan...")

# ── 7. MAIN LOGIC ──────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_dashboard()
else:
    show_login()