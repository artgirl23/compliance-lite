import streamlit as st
from supabase import create_client, Client

# ── 1. PAGE SETUP (Keeps login centered like Screenshot 172208) ───────────────
st.set_page_config(page_title="Compliance Lite", layout="centered", page_icon="🛡️")

# ── 2. SESSION STATE ──────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ── 3. DATABASE ───────────────────────────────────────────────────────────────
@st.cache_resource
def _get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── 4. STYLES (Pixel-matched to Screenshot 172208 and 183807) ─────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f172a !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { display: none !important; }

    /* The Centered Login Card */
    .login-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 28px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-top: 20px;
    }

    /* The Main Header Banner (Screenshot 183807) */
    .main-header {
        background: #3b82f6 !important;
        padding: 60px;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 30px;
        color: white !important;
    }

    /* Red Action Buttons */
    div:not([data-testid="stSidebar"]) button {
        background-color: #ef4444 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 700 !important;
    }

    /* Sidebar Dark Theme */
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
</style>
""", unsafe_allow_html=True)

# ── 5. LOGIN SCREEN ───────────────────────────────────────────────────────────
def show_login():
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
    st.markdown("</div>", unsafe_allow_html=True)

# ── 6. DASHBOARD ──────────────────────────────────────────────────────────────
def show_dashboard():
    # Injects wide-mode ONLY after login to prevent stretching the card earlier
    st.markdown("<style>.block-container { max-width: 1400px !important; }</style>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.write("### Admin Portal")
        st.write("**Operator:** Katie Gray")
        st.write("**Role:** Marketing & UX Lead")
        if st.button("Sign Out"):
            st.session_state.authenticated = False
            st.rerun()

    st.markdown('<div class="main-header"><h1>🛡️ Compliance Lite</h1><p>Enterprise PHI Detection & Secure Cloud Auditing</p></div>', unsafe_allow_html=True)

    st.subheader("📁 Batch Upload")
    st.file_uploader("Drag and drop files here", accept_multiple_files=True)
    st.button("🛡️ Sanitize & Log Batch")

    st.markdown("---")
    st.subheader("● HISTORICAL COMPLIANCE AUDIT LOG")
    
    # CORRECTED: Changed table from scan_logs to scan_history per Screenshot 183807
    try:
        data = _get_supabase().table("scan_history").select("*").order('created_at', descending=True).execute()
        if data.data:
            st.dataframe(data.data, use_container_width=True)
        else:
            st.write("No audit records found for this account.")
    except Exception as e:
        st.error(f"Audit log error: {e}")

# ── 7. MAIN LOGIC ──────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_dashboard()
else:
    show_login()