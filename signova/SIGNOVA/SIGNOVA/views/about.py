import streamlit as st

from signova import __version__, ui

ui.page_header("About and privacy", f"SIGNOVA version {__version__}")

st.markdown("### Privacy")
st.markdown(
    """
- Camera frames are read and analysed on this computer by OpenCV and MediaPipe. They are not uploaded anywhere.
- Video and images are never written to disk. Only the text you choose to save goes into `data/signova.db`.
- Stopping the camera, leaving the Converter page or closing the app releases the webcam.
- Streamlit usage statistics are switched off in `.streamlit/config.toml`.
- Because the webcam is opened by the Python process, SIGNOVA is meant to run on your own PC (`localhost`), not on a remote server.
"""
)

st.markdown("### Honest limits")
st.markdown(
    """
- **Not a sign-language translator.** SIGNOVA recognises a small, app-defined gesture vocabulary. Real sign languages
  are not covered.
- **The percentage is a match-quality score, not an accuracy figure.** It measures how clearly each finger is extended
  or curled for the chosen pose. It is not a probability, and no accuracy claim is made for real users.
- **Tested with synthetic landmarks, not a user study.** Automated tests prove the rules and the hold/motion logic
  behave as designed. Real-world results depend on lighting, camera, hand shape and distance; you can tune the
  thresholds (see the README).
- One hand drives the text. With two hands visible, both are drawn but only the primary hand adds words.
"""
)

st.markdown("### Technology")
st.markdown(
    """
| Layer | Tool |
|---|---|
| Interface | Streamlit (all pages written in Python) |
| Camera and drawing | OpenCV |
| Hand landmarks | MediaPipe Hands (21 points per hand) |
| Numerics | NumPy |
| Storage | SQLite (`sqlite3` in the Python standard library) |
| Speech | pyttsx3 system voice, with a browser voice fallback |
"""
)
