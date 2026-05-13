import streamlit as st
import zipfile
import io
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from supabase import create_client, Client
from src.services import process_compliance_scan
from pdf_generator import create_compliance_report




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
    st.session_state.user_id = None           # Supabase UUID — never an email
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0         # Increment to reset file uploader
if "last_activity" not in st.session_state:
    st.session_state.last_activity = datetime.now()
if "user_role" not in st.session_state:
    st.session_state.user_role = "Admin"   # default; overridden by sidebar toggle




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
  /* Sidebar text → light gray (do NOT target div — that breaks toggle internals) */
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3,
  [data-testid="stSidebar"] h4,
  [data-testid="stSidebar"] label { color: #d1d5db !important; }


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


  /* SIDEBAR TOGGLE VISIBILITY FIX: Targets both collapsed and expanded states */
  [data-testid="collapsedControl"],
  button[data-testid="stSidebarCollapseButton"] {
    background-color: #334155 !important;
    border: 1px solid #64748b !important;
    border-radius: 6px !important;
    opacity: 1 !important;
    color: #ffffff !important;
  }
  [data-testid="collapsedControl"]:hover,
  button[data-testid="stSidebarCollapseButton"]:hover {
    background-color: #475569 !important;
  }
  /* Force toggle arrow SVG to white — default, hover, and all child paths */
  [data-testid="collapsedControl"] svg,
  [data-testid="collapsedControl"]:hover svg,
  button[data-testid="stSidebarCollapseButton"] svg,
  button[data-testid="stSidebarCollapseButton"]:hover svg {
    fill: #ffffff !important;
    stroke: #ffffff !important;
    color: #ffffff !important;
  }
  [data-testid="collapsedControl"] svg path,
  [data-testid="collapsedControl"]:hover svg path,
  button[data-testid="stSidebarCollapseButton"] svg path,
  button[data-testid="stSidebarCollapseButton"]:hover svg path {
    fill: #ffffff !important;
    stroke: #ffffff !important;
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


  /* FORCE SIDEBAR TO BE VISIBLE */
  [data-testid='stSidebar'][aria-expanded='false'] {
    margin-left: 0px !important;
    transform: none !important;
    width: 260px !important;
  }
/* Target the button identified in your screenshot */
[data-testid="stBaseButton-headerNoPadding"] {
    background-color: transparent !important;
    border: none !important;
    cursor: pointer !important;
}


/* Force the icon font color to white */
[data-testid="stIconMaterial"] {
    color: #ffffff !important;
}
/* Fix metric text color */
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: #f8fafc !important;
}
/* === EXPANDER HEADER HOVER — keep dark bg so risk badge text stays legible === */
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:focus {
    background-color: #1e293b !important;
    color: #f8fafc !important;
}
[data-testid="stExpander"] summary {
    background-color: #0f172a !important;
    color: #f8fafc !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #f8fafc !important;
}
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
<div style='display: flex; flex-direction: column; align-items: center; width: 100%; text-align: center;'>
    <div style='font-size: 3.5rem; margin-bottom: 15px;'>🛡️</div>
    <div style='margin-left: 4px;'>
        <h1 style='margin: 0; padding: 0; line-height: 1.2;'>Compliance Lite</h1>
        <p style='margin: 5px 0 25px 0; color: #94a3b8;'>Enterprise PHI Detection</p>
    </div>
</div>
""", unsafe_allow_html=True)


    email    = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")


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






# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def show_dashboard():
    st.markdown("""
    <script>
        const btn = window.parent.document.querySelector('[data-testid="collapsedControl"] button');
        if (btn) btn.click();
    </script>
    """, unsafe_allow_html=True)

    # ── 10-minute PHI inactivity lock ─────────────────────────────────────────
    _now = datetime.now()
    _last = st.session_state.get("last_activity")
    if _last and (_now - _last) > timedelta(minutes=10) and st.session_state.scan_result:
        st.session_state.scan_result  = None
        st.session_state.uploader_key += 1
        st.warning("⏱ Session inactive for 10 minutes — scan results cleared to protect PHI.")
    st.session_state.last_activity = _now

    user_email = st.session_state.get("user_email") or "demo@katiegray.design"


    # ── Sidebar — very first thing, no conditionals ───────────────────────────
    with st.sidebar:
        st.markdown("🛡️")
        st.markdown("### Admin Portal")

        _is_admin    = st.session_state.user_role == "Admin"
        _badge_color = "#D97706" if _is_admin else "#94a3b8"   # Gold / Gray
        _badge_label = "ADMIN"   if _is_admin else "OPERATOR"

        st.markdown(f"""
        <p style="font-size:0.7rem;color:#93c5fd;text-transform:uppercase;font-weight:700;margin:14px 0 2px;">OPERATOR</p>
        <p style="margin:0;color:#ffffff;">Katie Gray&nbsp;<span style="font-size:0.6rem;font-weight:700;color:{_badge_color};border:1px solid {_badge_color};border-radius:4px;padding:1px 6px;vertical-align:middle;">{_badge_label}</span></p>
        <p style="font-size:0.7rem;color:#93c5fd;text-transform:uppercase;font-weight:700;margin:12px 0 2px;">ROLE</p>
        <p style="margin:0;color:#ffffff;">Marketing &amp; UX Lead</p>
        <p style="font-size:0.7rem;color:#93c5fd;text-transform:uppercase;font-weight:700;margin:12px 0 2px;">ACCOUNT</p>
        <p style="margin:0;color:#ffffff;">{user_email}</p>
        <p style="color:#60a5fa;font-size:0.85rem;margin-top:10px;">● Cloud Connected</p>
        """, unsafe_allow_html=True)

        st.write("")
        st.radio(
            "View App As:",
            options=["Admin", "Operator"],
            key="user_role",
            horizontal=True,
        )
        st.write("")

        if st.button("📋 New Batch Scan", use_container_width=True):
            st.session_state.scan_result  = None
            st.session_state.uploader_key += 1
            st.rerun()
        if st.button("Sign Out", use_container_width=True, type="primary"):
            st.session_state.clear()
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
                        result    = process_compliance_scan(content)
                        phi_count = len(result["phones"]) + len(result["emails"])
                        risk      = result.get("risk_level", "LOW")  # HIGH ≥4 / MEDIUM 1-3 / LOW 0
                        get_supabase().table("scan_history").insert({
                            "filename":       f.name,
                            "risk_status":    risk,
                            "phi_count":      phi_count,
                            "user_id":        st.session_state.user_id,
                            "file_hash":      result["hash"],            # <--- ADD THIS
                            "sanitized_text": result["sanitized_text"],  # <--- ADD THIS
                        }).execute()
                        processed_files.append({
                                "name":      f.name,
                                "sanitized": result["sanitized_text"],
                                "risk":      risk,
                                "phi_count": phi_count,
                                "phone_count": len(result["phones"]), # Added
                                "email_count": len(result["emails"]), # Added
                                "risk_summary": result.get("risk_summary"),
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
        st.subheader("Batch Executive Summary")
        r = st.session_state.scan_result
        total_phones = sum(f['phone_count'] for f in r['files'])
        total_emails = sum(f['email_count'] for f in r['files'])
        risk_score = (total_phones * 10) + (total_emails * 5)
       
        col1, col2, col3 = st.columns(3)
        col1.metric("Risk Score", risk_score)
        col2.metric("Phones Found", total_phones)
        col3.metric("Emails Found", total_emails)
       
        # Create cleaner, aligned Plotly chart
        chart_data = pd.DataFrame({"Type": ["Phones", "Emails"], "Count": [total_phones, total_emails]})
       
        fig = px.bar(
            chart_data,
            x="Type",
            y="Count",
            color="Type",
            template="plotly_dark",
            text="Count"
        )
       
        # Style the chart for your dashboard
        fig.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=30, b=20),
            height=300
        )
       
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        r = st.session_state.scan_result

        _RANK       = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        batch_risk  = max((f["risk"] for f in r["files"]), key=lambda x: _RANK.get(x, 0), default="LOW")
        is_high_risk   = batch_risk == "HIGH"
        is_medium_risk = batch_risk == "MEDIUM"
        total_phi      = sum(f["phi_count"] for f in r["files"])

        # Weighted compliance score: clean files / total files × 100
        _total_files    = len(r["files"])
        _files_with_phi = sum(1 for f in r["files"] if f["phi_count"] > 0)
        _score_pct      = int(round((_total_files - _files_with_phi) / _total_files * 100)) if _total_files else 100
        _score          = f"{_score_pct}%"
        _level          = "⚠️ HIGH" if is_high_risk else ("🟡 MEDIUM" if is_medium_risk else "✅ LOW")

        with st.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("Compliance Score", _score)
            m2.metric("Risk Level", _level)
            m3.metric("PII/PHI Findings", total_phi)

        if r["errors"]:
            st.error("Errors: " + "; ".join(r["errors"]))

        if r["count"] > 0:
            summary_msg = f"✅ {r['count']} file(s) sanitized and logged."
            if is_high_risk:
                st.error(summary_msg)
            elif is_medium_risk:
                st.warning(summary_msg)
            else:
                st.success(summary_msg)


            # Per-file redacted preview
            for fd in r["files"]:
                if fd["risk"] == "HIGH":
                    risk_badge = "🔴 HIGH RISK"
                elif fd["risk"] == "MEDIUM":
                    risk_badge = "🟡 MEDIUM RISK"
                else:
                    risk_badge = "🟢 LOW RISK"
                label = (
                    f"{risk_badge} · {fd['name']}  "
                    f"[{fd['phi_count']} PHI item(s)]"
                )
                with st.expander(label):
                    st.code(fd["sanitized"], language=None)
                    if fd.get("risk_summary"):
                      st.markdown(f"**Compliance Insight:** {fd['risk_summary']}")


            # Build ZIP in memory
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for fd in r["files"]:
                    zf.writestr(f"sanitized_{fd['name']}", fd["sanitized"])
            zip_buf.seek(0)


            # (NEW CODE YOU ARE PASTING)
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                downloaded = st.download_button(
                    label="⬇ Download ZIP",
                    data=zip_buf,
                    file_name="sanitized_batch.zip",
                    mime="application/zip",
                    use_container_width=True,
                )
            with btn_col2:
                pdf_data = create_compliance_report(st.session_state.scan_result)
                st.download_button(
                    label="📄 Download Report",
                    data=pdf_data,
                    file_name="batch_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            with btn_col3:
                clear_clicked = st.button("🗑 Clear Batch", use_container_width=True, type="secondary")

            if clear_clicked:
                st.session_state.scan_result = None
                st.session_state.uploader_key += 1
                st.rerun()


    # ── Audit Log (Admin only) ────────────────────────────────────────────────
    st.markdown("---")
    if st.session_state.user_role == "Admin":
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
                .select("id, created_at, filename, risk_status, phi_count, file_hash, sanitized_text")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
                .data
            )
            if rows:
                df_audit = pd.DataFrame(rows)
                csv = df_audit.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Audit Log (CSV)",
                    data=csv,
                    file_name="compliance_audit_log.csv",
                    mime="text/csv",
                )
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.write("No audit records found for this account.")
        except Exception as e:
            st.error(f"Audit log error: {e}")
    else:
        st.markdown(
            "<p style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;"
            "color:#475569;text-transform:uppercase;margin:0 0 12px;'>"
            "🔒 Audit Log — Admin Access Required</p>",
            unsafe_allow_html=True,
        )




# ── ROUTER ─────────────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    st.session_state.sidebar_state = 'expanded'
    show_dashboard()
else:
    show_login()
