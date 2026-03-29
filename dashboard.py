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
    st.session_state.user_id = None
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ── DATABASE ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# ── GLOBAL CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* === GLOBAL === */
  .stApp { background-color: #0f172a !important; color: #f8fafc !important; }

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

  /* FIX: Password eye icon - Clean blue outline, no background blob */
  [data-testid="stPasswordInputVisibilityToggle"], 
  [data-testid="stTextInput"] button {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }
  [data-testid="stPasswordInputVisibilityToggle"] svg,
  [data-testid="stTextInput"] button svg {
    fill: none !important;
    stroke: #3b82f6 !important;
    stroke-width: 2 !important;
    color: #3b82f6 !important;
  }

  /* === SIDEBAR === */
  [data-testid="stSidebar"],
  [data-testid="stSidebar"] > div:first-child {
    background-color: #0f172a !important;
  }
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3,
  [data-testid="stSidebar"] h4,
  [data-testid="stSidebar"] label { color: #ffffff !important; }

  /* Sidebar buttons */
  [data-testid="stSidebar"] button {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
  }
  [data-testid="stSidebar"] button[kind="primary"] {
    background-color: #ef4444 !important;
    color: #ffffff !important;
    border: none !important;
  }

  /* FIX: THE LIGHT GRAY TOGGLE ARROW (VISIBLE WHEN COLLAPSED) */
  [data-testid="collapsedControl"] svg,
  button[data-testid="stSidebarCollapseByFrame"] svg,
  [data-testid="stSidebarCollapseButton"] svg {
    fill: #d1d5db !important;
    color: #d1d5db !important;
    stroke: #d1d5db !important;
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

  /* === LOGIN CARD CENTERING FIX === */
  .login-header, .login-header * {
    text-align: center !important;
    width: 100% !important;
    display: block !important;
  }
</style>
""", unsafe_allow_html=True)


# ── LOGIN ──────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <style>
      .block-container {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 28px !important;
        padding: 50px 40px !important;
        max-width: 450px !important;
        margin: auto !important;
      }
      /* Center all markdown text in the login modal */
      .block-container [data-testid="stMarkdownContainer"],
      .block-container [data-testid="stMarkdownContainer"] p,
      .block-container [data-testid="stMarkdownContainer"] h1 {
        text-align: center !important;
        display: block !important;
        width: 100% !important;
      }
      /* Force Sign In button to Blue */
      .block-