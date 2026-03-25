import streamlit as st
from supabase import create_client, Client

# ── 1. PAGE SETUP ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Compliance Lite", layout="wide", page_icon="🛡️")

# ── 2. SESSION STATE ──────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ── 3. DATABASE ───────────────────────────────────────────────────────────────
@st.cache_resource
def _get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── 4. STYLES (Restored From Your Screenshots) ────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f172a !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { display: none !important; }

    /* Centered Login Card */
    .login-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 28px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }

    /* Main Blue Header Banner */
    .main-header {
        background: #3b82f6 !important;
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        color: white !important;
    }

    /* Standard Buttons */
    div:not([data-testid="stSidebar"]) button {
        background-color: #3b82f6 !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar Logout Button Red */
    [data-testid="stSidebar"] button {
        background-color: #ef4444 !important;
        color: white !important;
    }

    /* Dark Sidebar */
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
</style>
""", unsafe_allow_html=True)

# ── 5. LOGIN SCREEN ───────────────────────────────────────────────────────────
def show_login():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
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
        
        st.markdown("<small>demo@katiegray.design | Compliance2026</small></div>", unsafe_allow_html=True)

# ── 6. DASHBOARD ──────────────────────────────────────────────────────────────
def show_dashboard():
    with st.sidebar:
        st.write("### Admin Portal")
        st.write("**Operator:** Katie Gray")
        st.write("**Account:** demo@katiegray.design")
        if st.button("Sign Out"):
            st.session_state.authenticated = False
            st.rerun()

    st.markdown('<div class="main-header"><h1>🛡️ Compliance Lite</h1><p>Enterprise PHI Detection</p></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Batch Processing")
        st.file_uploader("Upload Files", accept_multiple_files=True)
        if st.button("🛡️ Sanitize & Log Batch"):
            st.info("Scanner logic active.")

    with c2:
        st.subheader("Recent Activity Audit Log")
        st.write("System Ready.")

# ── 7. MAIN LOGIC ──────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_dashboard()
else:
    show_login()