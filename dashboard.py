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
    st.session_state.user_id = None          # Supabase UUID — never an email
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0        # Increment to reset file uploader


# ── DATABASE ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


# ── GLOBAL CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* === GLOBAL === */
  .stApp { background-color: #0f172a !important; color: #f8fafc !important; }


  /* Header: transparent — do NOT hide stHeader (it holds the sidebar toggle) */
  [data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
  }
  [data-testid="stDecoration"] { display: none !important; }


  /* === TEXT INPUTS === */
  [data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
  }
  [data-testid="stTextInput"] label { color: #94a3b8 !important; font-size: 0.85rem !important; }
  /* Password eye icon: transparent bg, blue icon — remove the solid blue box */
  [data-testid="stTextInput"] button {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }
  [data-testid="stTextInput"] button svg {
    fill: #3b82f6 !important;
    stroke: #3b82f6 !important;
  }


  /* === SIDEBAR — minimal: only color, no layout overrides === */
  [data-testid="stSidebar"],
  [data-testid="stSidebar"] > div:first-child {
    background-color: #0f172a !important;
  }
  /* Sidebar text → white (do NOT target div — that breaks toggle internals) */
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3,
  [data-testid="stSidebar"] h4,
  [data-testid="stSidebar"] label { color: #ffffff !important; }


  /* Sidebar buttons: dark outlined (New Batch Scan) */
  [data-testid="stSidebar"] button {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
  }
  /* Sign Out (type="primary") → red. Both selectors for version compatibility. */
  [data-testid="stSidebar"] button[kind="primary"],
  [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
    background-color: #ef4444 !important;
    color: #ffffff !important;
    border: none !important;
  }


  /* Sidebar button hover states */
  [data-testid="stSidebar"] button:hover {
    background-color: #334155 !important;
    transition: background-color 0.15s ease !important;
  }
  [data-testid="stSidebar"] button[kind="primary"]:hover,
  [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover {
    background-color: #f87171 !important;
    transition: background-color 0.15s ease !important;
  }


  /* Sidebar collapse/expand toggle buttons */
  [data-testid="stSidebarCollapseButton"] button,
  [data-testid="stSidebarCollapsedControl"] button,
  [data-testid="collapsedControl"] button,
  [data-testid="stSidebarCollapseByFrame"] button {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
    color: #d1d5db !important; /* sets currentColor for SVGs that use it */
  }
  /* Arrow SVG → #d1d5db light gray. Targets svg, path, and all children
     to catch both fill="currentColor" and explicit fill attributes. */
  [data-testid="collapsedControl"] svg,
  [data-testid="collapsedControl"] svg path,
  [data-testid="collapsedControl"] svg *,
  button[data-testid="stSidebarCollapseByFrame"] svg,
  button[data-testid="stSidebarCollapseByFrame"] svg path,
  button[data-testid="stSidebarCollapseByFrame"] svg *,
  [data-testid="stSidebarCollapseButton"] button svg,
  [data-testid="stSidebarCollapseButton"] button svg path,
  [data-testid="stSidebarCollapsedControl"] svg,
  [data-testid="stSidebarCollapsedControl"] svg path {
    fill: #d1d5db !important;
    stroke: #d1d5db !important;
    color: #d1d5db !important;
  }


  /* === DASHBOARD BANNER === */
  .main-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #3b82f6 100%);
    border-radius: 24px;
    padding: 48px 40px;
    margin-bottom: 28px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .main-banner h1 {
    color: white !important;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 8px 0 6px;
    text-align: center !important;
    width: 100% !important;
  }
  .main-banner p {
    color: rgba(255,255,255,0.85) !important;
    font-size: 1rem;
    margin: 0;
    text-align: center !important;
  }


  /* === DOWNLOAD BUTTON → blue (stable data-testid selector) === */
  [data-testid="stDownloadButton"] button,
  .stDownloadButton button {
    background-color: #3b82f6 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
  }


  /* === FILE UPLOADER === */
  [data-testid="stFileUploader"] section {
    background-color: #1e293b !important;
    border: 2px solid #475569 !important;
    border-radius: 12px !important;
  }
  [data-testid="stFileUploaderDropzoneInstructions"],
  [data-testid="stFileUploaderDropzoneInstructions"] span,
  [data-testid="stFileUploaderDropzoneInstructions"] small,
  [data-testid="stFileUploader"] section p,
  [data-testid="stFileUploader"] section span,
  [data-testid="stFileUploader"] section small { color: #e2e8f0 !important; }
  [data-testid="stFileUploaderFile"],
  [data-testid="stFileUploaderFileName"],
  [data-testid="stFileUploader"] span,
  [data-testid="stFileUploader"] p,
  [data-testid="stFileUploader"] small { color: #e2e8f0 !important; }
  [data-testid="stFileUploaderDeleteBtn"] button {
    background-color: transparent !important;
    border: none !important;
    color: #94a3b8 !important;
    border-radius: 50% !important;
    box-shadow: none !important;
  }
  [data-testid="stFileUploaderDeleteBtn"] button svg {
    fill: #94a3b8 !important;
    stroke: #94a3b8 !important;
  }


  /* === LOGIN CARD CENTERING === */
  .login-header { text-align: center !important; width: 100% !important; }
  .login-header * { text-align: center !important; }
</style>
""", unsafe_allow_html=True)




# ── LOGIN ──────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <style>
      .st-emotion-cache-z5fcl4, .st-emotion-cache-13ln4jf,
      [data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; }
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
      /* LOGIN PAGE: Sign In button → blue. Both selectors for version compatibility. */
      .block-container button,
      .block-container button[kind="secondary"],
      .block-container button[data-testid="stBaseButton-secondary"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
      }
      /* Center login text: target Streamlit's own markdown wrapper which sits above
         .login-header and applies text-align:left by default */
      .block-container [data-testid="stMarkdownContainer"],
      .block-container [data-testid="stMarkdownContainer"] h1,
      .block-container [data-testid="stMarkdownContainer"] h2,
      .block-container [data-testid="stMarkdownContainer"] h3,
      .block-container [data-testid="stMarkdownContainer"] p,
      .login-header,
      .login-header h1,
      .login-header p {
        text-align: center !important;
        width: 100% !important;
      }
      /* Exception: password eye icon must NOT get the blue background */
      [data-testid="stTextInput"] button,
      [data-testid="stPasswordInputVisibilityToggle"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: transparent !important;
      }
      [data-testid="stTextInput"] button svg,
      [data-testid="stPasswordInputVisibilityToggle"] svg {
        fill: #3b82f6 !important;
        stroke: #3b82f6 !important;
      }
    </style>
    """, unsafe_allow_html=True)


    st.markdown("""
    <div class="login-header" style="text-align:center; padding-bottom:20px; width:100%;">
      <div style="display:flex; justify-content:center; align-items:center; width:100%;">
        <span style="font-size:3.5rem; display:block;">🛡️</span>
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


    email    = st.text_input("Email", value="demo@katiegray.design", key="login_email")
    password = st.text_input("Password", type="password", value="Compliance2026", key="login_pass")


    st.markdown('<div class="login-signin">', unsafe_allow_html=True)
    if st.button("Sign In →", use_container_width=True):
        try:
            response = get_supabase().auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if response.user:
                st.session_state.authenticated = True
                st.session_state.user_email    = email
                st.session_state.user_id       = response.user.id  # UUID
                st.rerun()
            else:
                st.error("Authentication failed. Please check your credentials.")
        except Exception as e:
            st.error(f"System Error: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)


    st.markdown(
        "<p style='text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:15px;'>"
        "demo@katiegray.design | Compliance2026</p>",
        unsafe_allow_html=True,
    )




# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def show_dashboard():
    user_email = st.session_state.get("user_email") or "demo@katiegray.design"


    # ── Sidebar — very first thing, no conditionals ───────────────────────────
    with st.sidebar:
        st.markdown("🛡️")
        st.markdown("### Admin Portal")
        st.markdown(f"""
        <p style="font-size:0.7rem;color:#93c5fd;text-transform:uppercase;font-weight:700;margin:14px 0 2px;">OPERATOR</p>
        <p style="margin:0;color:#ffffff;">Katie Gray</p>
        <p style="font-size:0.7rem;color:#93c5fd;text-transform:uppercase;font-weight:700;margin:12px 0 2px;">ROLE</p>
        <p style="margin:0;color:#ffffff;">Marketing &amp; UX Lead</p>
        <p style="font-size:0.7rem;color:#93c5fd;text-transform:uppercase;font-weight:700;margin:12px 0 2px;">ACCOUNT</p>
        <p style="margin:0;color:#ffffff;">{user_email}</p>
        <p style="color:#60a5fa;font-size:0.85rem;margin-top:10px;">● Cloud Connected</p>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("📋 New Batch Scan", use_container_width=True):
            st.session_state.scan_result  = None
            st.session_state.uploader_key += 1
            st.rerun()
        if st.button("Sign Out", use_container_width=True, type="primary"):
            st.session_state.authenticated = False
            st.session_state.user_email    = ""
            st.session_state.user_id       = None
            st.session_state.scan_result   = None
            st.rerun()


    # Dashboard container + button color overrides
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
      /* Sanitize (type="primary") → red */
      .block-container button[kind="primary"],
      .block-container button[data-testid="stBaseButton-primary"] {
        background-color: #ef4444 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
      }
      .block-container button[kind="primary"]:hover,
      .block-container button[data-testid="stBaseButton-primary"]:hover {
        background-color: #dc2626 !important;
      }
      /* Clear Batch (type="secondary") → medium gray + white text */
      .block-container button[kind="secondary"],
      .block-container button[data-testid="stBaseButton-secondary"] {
        background-color: #64748b !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
      }
      .block-container button[kind="secondary"]:hover,
      .block-container button[data-testid="stBaseButton-secondary"]:hover {
        background-color: #475569 !important;
      }
      /* Download button → blue.
         Uses .block-container prefix to match specificity (0,2,1) of the secondary rule above,
         then wins by cascade position (comes after). */
      .block-container [data-testid="stDownloadButton"] button,
      .stDownloadButton button {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
      }
      .block-container [data-testid="stDownloadButton"] button:hover,
      .stDownloadButton button:hover {
        background-color: #2563eb !important;
      }
    </style>
    """, unsafe_allow_html=True)


    # ── Banner ────────────────────────────────────────────────────────────────
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
        key=f"batch_uploader_{st.session_state.uploader_key}",
    )


    if st.button("🛡️ Sanitize & Log Batch", type="primary"):
        if not uploaded_files:
            st.warning("Please upload at least one file first.")
        else:
            st.session_state.scan_result = None
            with st.spinner("Scanning for PHI..."):
                errors, count, processed_files = [], 0, []
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
                            "user_id":     st.session_state.user_id,  # UUID
                        }).execute()
                        processed_files.append({
                            "name":      f.name,
                            "sanitized": result["sanitized_text"],
                            "risk":      risk,
                            "phi_count": phi_count,
                        })
                        count += 1
                    except Exception as e:
                        errors.append(f"{f.name}: {e}")
            st.session_state.scan_result = {
                "count":  count,
                "errors": errors,
                "files":  processed_files,
            }
            st.rerun()


    # ── Results: success → previews → download → clear ────────────────────────
    if st.session_state.scan_result:
        r = st.session_state.scan_result


        if r["errors"]:
            st.error("Errors: " + "; ".join(r["errors"]))


        if r["count"] > 0:
            st.success(f"✅ {r['count']} file(s) sanitized and logged.")


            # Per-file redacted preview
            for fd in r["files"]:
                label = (
                    f"👁 Preview Redacted: {fd['name']}  "
                    f"[{fd['risk']} — {fd['phi_count']} PHI item(s)]"
                )
                with st.expander(label):
                    st.code(fd["sanitized"], language=None)


            # Build ZIP in memory
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for fd in r["files"]:
                    zf.writestr(f"sanitized_{fd['name']}", fd["sanitized"])
            zip_buf.seek(0)


            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                downloaded = st.download_button(
                    label="⬇ Download Sanitized Batch (.zip)",
                    data=zip_buf,
                    file_name="sanitized_batch.zip",
                    mime="application/zip",
                    use_container_width=True,
                )
            with btn_col2:
                clear_clicked = st.button("🗑 Clear Batch", use_container_width=True, type="secondary")


            if downloaded or clear_clicked:
                st.session_state.scan_result  = None
                st.session_state.uploader_key += 1
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