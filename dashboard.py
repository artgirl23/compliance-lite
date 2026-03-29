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
    width: 100% !important