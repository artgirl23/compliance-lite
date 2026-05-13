# Compliance Lite: Master Architectural & Design Rules

## UI/UX Rendering Protocol (Strict)
1. **NO INLINE CSS:** Never use `<div style="...">` inside any Python functions. It causes layout leakage.
2. **CENTRALIZED STYLING:** All CSS must be contained in a single `st.markdown("<style>...</style>", unsafe_allow_html=True)` block at the very top of `dashboard.py`.
3. **CONTAINER-SAFE SELECTORS:** Use `[data-testid="..."]` to target elements.
4. **LOGIN CARD:** Must be a centered 450px card with:
   - `background: rgba(255, 255, 255, 0.05)`
   - `backdrop-filter: blur(12px)`
   - `border: 1px solid rgba(255, 255, 255, 0.1)`
   - `margin: auto`
5. **VISIBILITY FIXES:** - Login Button: Background `#3b82f6` (blue), text `white`.
   - Sidebar Arrow (`[data-testid="collapsedControl"]`): Must have a light background and white SVG icon to ensure visibility against the dark slate sidebar.

## Functional Standards
- Do NOT alter business logic, Supabase authentication, or file scanning imports. 
- Only update UI/CSS/Layout code.