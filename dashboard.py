import streamlit as st
from supabase import create_client, Client
from scanner import scan_for_phi

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Compliance Lite", layout="centered", page_icon="🛡️")

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# ── DATABASE ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── GLOBAL CSS (dark page, hide header) ───────────────────────────────────────
st.markdown("""
<style>
  .stApp { background-color: #0f172a !important; color: #f8fafc !important; }
  [data-testid="stHeader"] { display: none !important; }

  /* White inputs with dark text */
  [data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
  }
  [data-testid="stTextInput"] label { color: #94a3b8 !important; font-size: 0.85rem !important; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #1e293b !important;
  }
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] div { color: #f8fafc; }

  /* All sidebar buttons = red (only Sign Out lives there) */
  [data-testid="stSidebar"] button {
    background-color: #ef4444 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    width: 100% !important;
  }

  /* Dashboard banner */
  .main-banner {
    background: #3b82f6;
    border-radius: 24px;
    padding: 48px 40px;
    text-align: center;
    margin-bottom: 28px;
  }
  .main-banner h1 { color: white !important; font-size: 2.2rem; font-weight: 800; margin: 8px 0 6px; }
  .main-banner p  { color: rgba(255,255,255,0.85) !important; font-size: 1rem; margin: 0; }

  /* Sanitize / action buttons in main content */
  .block-container button {
    background-color: #ef4444 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
  }

  /* Sign In button is blue, not red */
  .login-signin button {
    background-color: #3b82f6 !important;
  }
</style>
""", unsafe_allow_html=True)


# ── LOGIN ──────────────────────────────────────────────────────────────────────
def show_login():
    # ── LOGIN SPECIFIC CSS (Fixes the Layout) ──
    st.markdown("""
    <style>
        /* Force the login card to be centered and clean */
        [data-testid="stAppViewContainer"] {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .block-container {
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 28px !important;
            padding: 50px 40px !important;
            max-width: 450px !important;
            margin: auto !important;
            position: relative !important;
            top: 50%;
            transform: translateY(20%);
        }
        /* Hide the top padding/header gap */
        [data-testid="stHeader"] { display: none !important; }
        div[data-testid="stVerticalBlock"] > div:first-child { margin-top: -50px !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding-bottom: 20px;">
      <span style="font-size:3.5rem;">🛡️</span>
      <h1 style="color:#f8fafc; font-weight:800; font-size:2rem; margin:10px 0 2px; letter-spacing:-0.02em;">
        Compliance Lite
      </h1>
      <p style="color:#94a3b8; font-size:1rem; margin:0; font-weight:400;">Enterprise PHI Detection</p>
    </div>
    """, unsafe_allow_html=True)

    # ── INPUTS ──
    email = st.text_input("Email", value="demo@katiegray.design", key="login_email")
    password = st.text_input("Password", type="password", value="Compliance2026", key="login_pass")

    st.markdown('<div class="login-signin">', unsafe_allow_html=True)
    if st.button("Sign In →", use_container_width=True):
        try:
            # We add a check to ensure Supabase is actually responding
            response = get_supabase().auth.sign_in_with_password({"email": email, "password": password})
            
            if response.user:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Authentication failed. Please check your credentials.")
        except Exception as e:
            # This will tell us if it's a password issue or a Connection issue
            st.error(f"System Error: {str(e)}")
            
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='text-align:center; color:#64748b; font-size:0.85rem; margin-top:20px; font-family:monospace;'>"
        "demo@katiegray.design | Compliance2026</p>",
        unsafe_allow_html=True,
    )


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def show_dashboard():
    # Expand centered layout to full width for dashboard
    st.markdown("""
    <style>
      .block-container {
        background: transparent !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 1.5rem 2rem !important;
        max-width: 1400px !important;
        margin-top: 0 !important;
      }
    </style>
    """, unsafe_allow_html=True)

    user_email = st.session_state.get("user_email") or "demo@katiegray.design"

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("🛡️")
        st.markdown("### Admin Portal")
        st.markdown(f"""
        <p style="font-size:0.7rem;color:#64748b;text-transform:uppercase;font-weight:700;margin:14px 0 2px;">OPERATOR</p>
        <p style="margin:0;">Katie Gray</p>
        <p style="font-size:0.7rem;color:#64748b;text-transform:uppercase;font-weight:700;margin:12px 0 2px;">ROLE</p>
        <p style="margin:0;">Marketing &amp; UX Lead</p>
        <p style="font-size:0.7rem;color:#64748b;text-transform:uppercase;font-weight:700;margin:12px 0 2px;">ACCOUNT</p>
        <p style="margin:0;">{user_email}</p>
        <p style="color:#22c55e;font-size:0.85rem;margin-top:10px;">● Cloud Connected</p>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = ""
            st.rerun()

    # ── Blue Banner ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="main-banner">
      <span style="font-size:2.2rem;">🛡️</span>
      <h1>Compliance Lite</h1>
      <p>Enterprise PHI Detection &amp; Secure Cloud Auditing</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Batch Upload ──────────────────────────────────────────────────────────
    st.markdown("**📁 Batch Upload**")
    uploaded_files = st.file_uploader(
        "Upload files for scanning",
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if st.button("🛡️ Sanitize & Log Batch"):
        if not uploaded_files:
            st.warning("Please upload at least one file first.")
        else:
            with st.spinner("Scanning and logging…"):
                errors, count = [], 0
                for f in uploaded_files:
                    try:
                        content   = f.read().decode("utf-8", errors="ignore")
                        result    = scan_for_phi(content)
                        phi_count = len(result["phones"]) + len(result["emails"])
                        risk      = "HIGH" if result["phi_found"] else "LOW"
                        get_supabase().table("scan_history").insert({
                            "filename":    f.name,
                            "risk_status": risk,
                            "phi_count":   phi_count,
                            "user_id":     user_email,
                        }).execute()
                        count += 1
                    except Exception as e:
                        errors.append(f"{f.name}: {e}")
            if errors:
                st.error("Errors: " + "; ".join(errors))
            else:
                st.success(f"✅ {count} file(s) sanitized and logged.")
            st.rerun()

    # ── Audit Log ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;"
        "color:#64748b;text-transform:uppercase;margin:0 0 12px;'>"
        "● Historical Compliance Audit Log</p>",
        unsafe_allow_html=True,
    )

    try:
        rows = (
            get_supabase()
            .table("scan_history")
            .select("id, created_at, filename, risk_status, phi_count")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
            .data
        )
        if rows:
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.write("No audit records found for this account.")
    except Exception as e:
        st.error(f"Audit log error: {e}")


# ── ROUTER ─────────────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_dashboard()
else:
    show_login()
