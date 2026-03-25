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

# ── 4. STYLES (The Original Vibe) ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp { background-color: #0f172a !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { display: none !important; }

    /* The Main Blue Banner */
    .main-header {
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        color: white !important;
    }

    /* Red Buttons (Main Area) */
    div:not([data-testid="stSidebar"]) button {
        background-color: #ef4444 !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #1e293b !important; }

    /* Browse Files Visibility */
    [data-testid="stFileUploadDropzoneInstructions"] div { color: #1E1E1E !important; }
</style>
""", unsafe_allow_html=True)

# ── 5. LOGIN SCREEN ───────────────────────────────────────────────────────────
def show_login():
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.write("# 🛡️ Compliance Lite")
        st.write("ENTER DEMO CREDENTIALS")
        
        email = st.text_input("Email", value="demo@katiegray.design")
        password = st.text_input("Password", type="password", value="Compliance2026")
        
        if st.button("Sign In →"):
            try:
                # Direct check against Supabase
                _get_supabase().auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.authenticated = True
                st.rerun()
            except Exception as e:
                st.error("Invalid Credentials")

# ── 6. DASHBOARD ──────────────────────────────────────────────────────────────
def show_dashboard():
    with st.sidebar:
        st.write("## Admin Portal")
        st.write("**Operator:** Katie Gray")
        if st.button("Sign Out"):
            st.session_state.authenticated = False
            st.rerun()

    st.markdown('<div class="main-header"><h1>🛡️ Compliance Lite</h1><p>Enterprise PHI Detection</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Batch Processing")
        st.file_uploader("Upload Files", accept_multiple_files=True)
        st.button("🛡️ Sanitize & Log Batch")

    with col2:
        st.subheader("Audit Log")
        st.write("System Ready.")

# ── 7. MAIN LOGIC ──────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_dashboard()
else:
    show_login()