import streamlit as st
from supabase import create_client, Client
from scanner import scan_for_phi

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Compliance Lite", layout="wide", page_icon="🛡️")

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# ── DATABASE ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── CSS ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* === GLOBAL === */
  .stApp { background-color: #0f172a !important; color: #f8fafc !important; }
  [data-testid="stHeader"] { display: none !important; }
  .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }

  /* === INPUTS === */
  [data-testid="stTextInput"] input {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
  }
  [data-testid="stTextInput"] label { color: #94a3b8 !important; font-size: 0.85rem !important; }

  /* === MAIN CONTENT BUTTONS (default = blue) === */
  .block-container button {
    background-color: #3b82f6 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
  }
  /* === MAIN CONTENT BUTTONS (primary = red, e.g. Sanitize) === */
  .block-container button[kind="primary"] {
    background-color: #ef4444 !important;
    color: white !important;
  }

  /* === SIDEBAR === */
  [data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid #1e293b !important;
  }
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span { color: #f8fafc; }

  /* Sidebar default buttons (New Batch Scan) = dark outline */
  [data-testid="stSidebar"] button {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
  }
  /* Sidebar primary button (Sign Out) = red */
  [data-testid="stSidebar"] button[kind="primary"] {
    background-color: #ef4444 !important;
    color: white !important;
    border: none !important;
  }

  /* === DASHBOARD BANNER === */
  .main-banner {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    border-radius: 20px;
    padding: 40px;
    text-align: center;
    margin-bottom: 24px;
  }
  .main-banner .banner-icon { font-size: 2.2rem; display: block; margin-bottom: 6px; }
  .main-banner h1 { color: white !important; font-size: 2.3rem; font-weight: 800; margin: 0 0 6px; }
  .main-banner p  { color: rgba(255,255,255,0.85) !important; font-size: 1rem; margin: 0; }

  /* === LOGIN CARD (via container border=True) === */
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(30, 41, 59, 0.95) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 28px !important;
    padding: 48px 40px 36px !important;
    margin-top: 60px !important;
  }

  /* === AUDIT LOG LABEL === */
  .audit-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #64748b;
    text-transform: uppercase;
    margin: 28px 0 12px;
  }

  /* === SIDEBAR META LABELS === */
  .meta-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #64748b;
    text-transform: uppercase;
    margin: 14px 0 3px;
    display: block;
  }
  .meta-value { font-size: 0.9rem; color: #f8fafc; display: block; margin: 0; }
  .cloud-badge { color: #22c55e; font-size: 0.85rem; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)


# ── LOGIN ──────────────────────────────────────────────────────────────────────
def show_login():
    _, col, _ = st.columns([3, 4, 3])
    with col:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align:center;padding:10px 0 20px;">
              <span style="font-size:3rem;">🛡️</span>
              <h1 style="color:#f8fafc;font-weight:700;font-size:1.85rem;margin:10px 0 4px;">
                Compliance Lite
              </h1>
              <p style="color:#94a3b8;font-size:0.9rem;margin:0 0 4px;">
                Enterprise PHI Detection
              </p>
            </div>
            """, unsafe_allow_html=True)

            email    = st.text_input("Email", value="demo@katiegray.design")
            password = st.text_input("Password", type="password", value="Compliance2026")

            if st.button("Sign In →", use_container_width=True):
                try:
                    get_supabase().auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.rerun()
                except Exception:
                    st.error("Invalid credentials. Please try again.")

            st.markdown(
                "<p style='text-align:center;color:#64748b;font-size:0.8rem;"
                "margin-top:16px;'>demo@katiegray.design&nbsp;|&nbsp;Compliance2026</p>",
                unsafe_allow_html=True,
            )


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def show_dashboard():
    user_email = st.session_state.get("user_email") or "demo@katiegray.design"

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("🛡️")
        st.markdown("### Admin Portal")
        st.markdown(f"""
        <span class="meta-label">OPERATOR</span>
        <span class="meta-value">Katie Gray</span>
        <span class="meta-label">ROLE</span>
        <span class="meta-value">Marketing &amp; UX Lead</span>
        <span class="meta-label">ACCOUNT</span>
        <span class="meta-value">{user_email}</span>
        <p class="cloud-badge">● Cloud Connected</p>
        """, unsafe_allow_html=True)

        st.write("")
        if st.button("📋 New Batch Scan", use_container_width=True):
            st.rerun()

        st.write("")
        if st.button("Sign Out", use_container_width=True, type="primary"):
            st.session_state.authenticated = False
            st.session_state.user_email = ""
            st.rerun()

    # ── Blue Banner ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="main-banner">
      <span class="banner-icon">🛡️</span>
      <h1>Compliance Lite</h1>
      <p>Enterprise PHI Detection &amp; Secure Cloud Auditing</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Batch Upload ──────────────────────────────────────────────────────────
    st.markdown("**📁 Batch Upload**")
    uploaded_files = st.file_uploader(
        "Upload files",
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if st.button("🛡️ Sanitize & Log Batch", type="primary"):
        if not uploaded_files:
            st.warning("Please upload at least one file first.")
        else:
            with st.spinner("Scanning and logging…"):
                errors = []
                count  = 0
                for f in uploaded_files:
                    try:
                        content   = f.read().decode("utf-8", errors="ignore")
                        result    = scan_for_phi(content)
                        phi_count = len(result["phones"]) + len(result["emails"])
                        risk      = "HIGH" if result["phi_found"] else "LOW"
                        get_supabase().table("scan_logs").insert({
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
    st.markdown(
        '<p class="audit-label">● Historical Compliance Audit Log</p>',
        unsafe_allow_html=True,
    )

    try:
        rows = (
            get_supabase()
            .table("scan_logs")
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
            st.markdown(
                "<p style='color:#64748b;font-size:0.9rem;'>"
                "No audit records found for this account.</p>",
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.markdown(
            f"<p style='color:#ef4444;font-size:0.9rem;'>Could not load audit log: {e}</p>",
            unsafe_allow_html=True,
        )


# ── ROUTER ─────────────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_dashboard()
else:
    show_login()
