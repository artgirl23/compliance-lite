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
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None

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
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #3b82f6 100%);
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

  /* ── File uploader: light text so filenames are readable ── */
  [data-testid="stFileUploaderFile"],
  [data-testid="stFileUploaderFileName"],
  [data-testid="stFileUploaderFileData"],
  [data-testid="stFileUploader"] span,
  [data-testid="stFileUploader"] p,
  [data-testid="stFileUploader"] small {
    color: #e2e8f0 !important;
  }

  /* ── File uploader delete button: subtle, no red circle ── */
  [data-testid="stFileUploaderDeleteBtn"] button {
    background-color: transparent !important;
    border: none !important;
    color: #94a3b8 !important;
    border-radius: 50% !important;
    padding: 2px 6px !important;
    font-size: 0.85rem !important;
    box-shadow: none !important;
  }
  [data-testid="stFileUploaderDeleteBtn"] button:hover {
    background-color: rgba(255, 255, 255, 0.1) !important;
    color: #f8fafc !important;
  }
  [data-testid="stFileUploaderDeleteBtn"] button svg {
    fill: #94a3b8 !important;
    stroke: #94a3b8 !important;
  }

  /* ── Login header: force horizontal centering ── */
  .login-header { text-align: center !important; width: 100% !important; }
  .login-header * { text-align: center !important; }

  /* ── Sidebar toggle chevron: always visible, brand blue ── */
  [data-testid="stSidebarCollapseButton"] button,
  [data-testid="stSidebarCollapsedControl"] button,
  button[data-testid="stBaseButton-headerNoPadding"] {
    background-color: #3b82f6 !important;
    border-radius: 8px !important;
    border: none !important;
    opacity: 1 !important;
    visibility: visible !important;
  }
  [data-testid="stSidebarCollapseButton"] button svg,
  [data-testid="stSidebarCollapsedControl"] svg,
  button[data-testid="stBaseButton-headerNoPadding"] svg {
    fill: white !important;
    stroke: white !important;
  }
  /* Keep toggle visible even when sidebar is collapsed */
  [data-testid="stSidebarCollapsedControl"] {
    background-color: #3b82f6 !important;
    border-radius: 8px !important;
    opacity: 1 !important;
    visibility: visible !important;
  }

  /* ── File uploader dropzone: dark navy background ── */
  [data-testid="stFileUploader"] section {
    background-color: #1e293b !important;
    border: 2px dashed #334155 !important;
    border-radius: 12px !important;
  }
  [data-testid="stFileUploaderDropzoneInstructions"],
  [data-testid="stFileUploaderDropzoneInstructions"] span,
  [data-testid="stFileUploaderDropzoneInstructions"] p,
  [data-testid="stFileUploaderDropzoneInstructions"] small,
  [data-testid="stFileUploader"] section p,
  [data-testid="stFileUploader"] section span,
  [data-testid="stFileUploader"] section small {
    color: #e2e8f0 !important;
  }

  /* ── Hover glow on all primary action buttons ── */
  .block-container button:hover {
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.6) !important;
    transition: box-shadow 0.2s ease !important;
  }
  [data-testid="stSidebar"] button:hover {
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.6) !important;
    transition: box-shadow 0.2s ease !important;
  }

  /* ── Dashboard banner: flex centering ── */
  .main-banner {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
  }
  .main-banner h1, .main-banner p, .main-banner span {
    text-align: center !important;
    width: 100% !important;
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
        /* Remove default top padding from emotion containers */
        .st-emotion-cache-z5fcl4, .st-emotion-cache-13ln4jf,
        [data-testid="stAppViewBlockContainer"] {
            padding-top: 0 !important;
        }
        /* Vertically center the login card */
        [data-testid="stAppViewContainer"] > section > div {
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 80vh;
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
        }
        [data-testid="stHeader"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-header" style="text-align:center; padding-bottom:20px; width:100%;">
      <div style="display:flex; justify-content:center; align-items:center; width:100%;">
        <span style="font-size:3.5rem; display:block; text-align:center;">🛡️</span>
      </div>
      <h1 style="color:#f8fafc; font-weight:800; font-size:2rem; margin:10px 0 2px;
                 letter-spacing:-0.02em; text-align:center; width:100%;">
        Compliance Lite
      </h1>
      <p style="color:#94a3b8; font-size:1rem; margin:0; font-weight:400; text-align:center;">
        Enterprise PHI Detection
      </p>
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
        "<p style='text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:15px;'>"
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
        <p style="color:#3b82f6;font-size:0.85rem;margin-top:10px;">● Cloud Connected</p>
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
        key="batch_uploader",
    )

    if st.button("🛡️ Sanitize & Log Batch"):
        if not uploaded_files:
            st.warning("Please upload at least one file first.")
        else:
            # Clear previous result before new scan
            st.session_state.scan_result = None
            with st.spinner("Scanning for PHI..."):
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
            # Persist result then rerun so audit log refreshes with new rows
            st.session_state.scan_result = {"count": count, "errors": errors}
            st.rerun()

    # Display last scan result (persists via session state)
    if st.session_state.scan_result:
        r = st.session_state.scan_result
        if r["errors"]:
            st.error("Errors: " + "; ".join(r["errors"]))
        else:
            st.success(f"✅ {r['count']} file(s) sanitized and logged.")

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
