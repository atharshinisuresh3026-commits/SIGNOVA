import streamlit as st

from signova import ui
from signova.gestures import DYNAMIC_GESTURES, STATIC_GESTURES

st.markdown(
    '<div class="sg-hero">'
    '<p class="sg-brand">SIGN<span>OVA</span></p>'
    '<p class="sg-sub">Real-Time Sign Language to Text Converter</p>'
    '<p class="sg-lede">Show a hand gesture to your webcam. SIGNOVA tracks 21 points on your hand, recognises it '
    'locally on your computer and writes the matching word into a sentence you can edit, save and have read aloud.</p>'
    '</div>',
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns([1.3, 1.3, 3])
if c1.button("Start Converting", type="primary", key="home_start"):
    st.switch_page("views/converter.py")
c2.page_link("views/guide.py", label="Gesture guide", icon="🖐️")

st.markdown(
    '<div class="sg-note"><b>What SIGNOVA recognises.</b> A small, fixed vocabulary of '
    f'{len(STATIC_GESTURES)} hand poses and {len(DYNAMIC_GESTURES)} hand motions, each mapped to a word chosen by this project. '
    'It is a gesture-to-text demo, not a full sign-language translator (ASL, ISL, BSL and others use two hands, '
    'facial expression and grammar that this app does not model).</div>',
    unsafe_allow_html=True,
)

st.markdown("### What you can do")
st.markdown(
    ui.grid(
        ui.card("📷", "Live camera", "Start and stop your webcam, with clear status and error messages if something is wrong."),
        ui.card("🖐️", "21-point hand tracking", "MediaPipe finds every joint; the skeleton is drawn over the video in real time."),
        ui.card("✋", "Pose recognition", "Open palm, fist, thumbs up, one, two and three fingers, and a love sign, each with a match-quality score."),
        ui.card("👋", "Motion gestures", "Wave and four swipe directions, recognised from how your palm moves across several frames."),
        ui.card("📝", "Text and speech", "Words build a sentence. Edit it, delete the last word, clear it, or have it read aloud."),
        ui.card("🗂️", "History and privacy", "Save sentences to a local SQLite database. Video is processed on your PC and never stored."),
    ),
    unsafe_allow_html=True,
)

st.markdown("### How it works")
st.markdown(
    ui.grid(
        ui.card("1", "Capture", "OpenCV reads frames from the webcam."),
        ui.card("2", "Track", "MediaPipe returns 21 landmarks per hand."),
        ui.card("3", "Recognise", "Finger angles and distances classify the pose; palm movement classifies motions."),
        ui.card("4", "Confirm", "A pose must be held about 0.8 seconds, so one hold adds one word."),
        ui.card("5", "Convert", "The word joins your sentence, ready to edit, speak or save."),
    ),
    unsafe_allow_html=True,
)
