"""SIGNOVA - Real-Time Sign Language to Text Converter (entry point).

Run with:  python -m streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="SIGNOVA - Sign Language to Text", page_icon="🖐️",
                   layout="wide", initial_sidebar_state="expanded")

from signova import __version__, ui  # noqa: E402  (must come after set_page_config)
from signova.state import init_state, stop_camera  # noqa: E402

ui.inject_css()
init_state()

pages = [
    st.Page("views/home.py", title="Home", icon="🏠", default=True),
    st.Page("views/converter.py", title="Converter", icon="🖐️"),
    st.Page("views/guide.py", title="Gesture guide", icon="📖"),
    st.Page("views/history.py", title="History", icon="🗂️"),
    st.Page("views/about.py", title="About and privacy", icon="🔒"),
]
page = st.navigation(pages)

# The webcam is only used on the Converter page: release it when the user leaves.
if page.title != "Converter" and st.session_state.get("running"):
    stop_camera()

st.sidebar.caption(f"SIGNOVA {__version__}. Camera frames stay on this computer.")
page.run()
