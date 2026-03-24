# Compliance Lite: Design Rules & Constraints

## UI/UX Standards
- **Layout:** Use `st.set_page_config(layout="wide")`.
- **Primary Color:** Use a consistent red (#EF4444) for all action buttons (like 'Sanitize' and 'New Batch Scan').
- **Sidebar:** Dark Slate (#1E293B) with all elements (logo, text, buttons) strictly left-aligned.
- **Header:** The main title/header must be flush with the top of the page; no significant white gap.
- **Main Content:** Left-aligned cards; no centered layout.

## Functional Goal
- **Next Phase:** Transition from hardcoded 'Katie Gray' `user_id` to dynamic user logic pulling from `st.session_state`.