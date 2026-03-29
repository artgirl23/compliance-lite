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

  /* Make header transparent (keep sidebar toggle functional — do NOT display:none) */
  [data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
  }
  /* Hide only the Streamlit toolbar/branding inside the header */
  [data-testid="stToolbar"],
  [data-testid="stDecoration"] {
    display: none !important;
  }

  /* === TEXT INPUTS === */
  [data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
  }
  [data-testid="stTextInput"] label { color: #94a3b8 !important; font-size: 0.85rem !important; }

  /* === SIDEBAR === */
  [data-testid="stSidebar"] {
    background-color: #0f172a !important;
    /* NO transform/min-width/max-width overrides — let Streamlit's toggle animate freely */
  }
  [data-testid="stSidebar"] > div:first-child {
    background-color: #0f172a !important;
    padding-top: 1.5rem !important;
  }
  /* Force ALL text in sidebar to be white/bright regardless of element type */
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3,
  [data-testid="stSidebar"] h4,
  [data-testid="stSidebar"] div,
  [data-testid="stSidebar"] label { color: #ffffff !important; }

  /* Sidebar buttons: dark outlined */
  [data-testid="stSidebar"] button {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
  }

  /* === MAIN CONTENT BUTTON COLORS === */
  /* Primary buttons (Sanitize & Log Batch) → red */
  .block-container button[kind="primary"] {
    background-color: #ef4444 !important;
    color: white !important;
    border: none !important;
  }
  /* Secondary buttons (Clear Batch) → medium gray */
  .block-container button[kind="secondary"] {
    background-color: #64748b !important;
    color: white !important;
    border: none !important;
  }

  /* Sidebar toggle: brand blue with drop shadow */
  [data-testid="stSidebarCollapseButton"] button,
  [data-testid="stSidebarCollapsedControl"] button,
  button[data-testid="stBaseButton-headerNoPadding"] {
    background-color: #3b82f6 !important;
    border-radius: 8px !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4) !important;
  }
  [data-testid="stSidebarCollapseButton"] button svg,
  [data-testid="stSidebarCollapsedControl"] svg,
  button[data-testid="stBaseButton-headerNoPadding"] svg {
    fill: white !important;
    stroke: white !important;
  }
  [data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: block !important;
    background-color: #3b82f6 !important;
    border-radius: 5px !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4) !important;
  }

  /* === DASHBOARD BANNER === */
  .main-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #3b82f6 100%);
    border-radius: 24px;
    padding: 48px 40px;
    text-align: center;
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

  /* === MAIN CONTENT BUTTONS (base) === */
  .block-container button {
    border-radius: 10px !important;
    font-weight: 700 !important;
  }

  /* Sign In is blue */
  .login-signin button {
    background-color: #3b82f6 !important;
    color: white !important;
    border: none !important;
  }

  /* Download button is brand blue (st.download_button renders as stDownloadButton) */
  .stDownloadButton button {
    background-color: #3b82f6 !important;
    color: white !important;
  }

  /* Hover glow */
  .block-container button:hover {
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.6) !important;
    transition: box-shadow 0.2s ease !important;
  }
  [data-testid="stSidebar"] button:hover {
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.6) !important;
    transition: box-shadow 0.2s ease !important;
  }

  /* === FILE UPLOADER === */
  /* Dropzone: dark navy, solid border */
  [data-testid="stFileUploader"] section {
    background-color: #1e293b !important;
    border: 2px solid #475569 !important;
    border-radius: 12px !important;
  }
  /* Dropzone instructional text */
  [data-testid="stFileUploaderDropzoneInstructions"],
  [data-testid="stFileUploaderDropzoneInstructions"] span,
  [data-testid="stFileUploaderDropzoneInstructions"] p,
  [data-testid="stFileUploaderDropzoneInstructions"] small,
  [data-testid="stFileUploader"] section p,
  [data-testid="stFileUploader"] section span,
  [data-testid="stFileUploader"] section small { color: #e2e8f0 !important; }
  /* Filename text */
  [data-testid="stFileUploaderFile"],
  [data-testid="stFileUploaderFileName"],
  [data-testid="stFileUploaderFileData"],
  [data-testid="stFileUploader"] span,
  [data-testid="stFileUploader"] p,
  [data-testid="stFileUploader"] small { color: #e2e8f0 !important; }
  /* Delete button: subtle X */
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
        <p style="font-size:0.7rem;color:#bfdbfe;text-transform:uppercase;font-weight:700;margin:14px 0 2px;">OPERATOR</p>
        <p style="margin:0;color:#ffffff;">Katie Gray</p>
        <p style="font-size:0.7rem;color:#bfdbfe;text-transform:uppercase;font-weight:700;margin:12px 0 2px;">ROLE</p>
        <p style="margin:0;color:#ffffff;">Marketing &amp; UX Lead</p>
        <p style="font-size:0.7rem;color:#bfdbfe;text-transform:uppercase;font-weight:700;margin:12px 0 2px;">ACCOUNT</p>
        <p style="margin:0;color:#ffffff;">{user_email}</p>
        <p style="color:#60a5fa;font-size:0.85rem;margin-top:10px;">● Cloud Connected</p>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("📋 New Batch Scan", use_container_width=True):
            st.session_state.scan_result  = None
            st.session_state.uploader_key += 1
            st.rerun()
        st.markdown('<div class="sign-out-btn">', unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email    = ""
            st.session_state.user_id       = None
            st.session_state.scan_result   = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Expand block-container for dashboard
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
