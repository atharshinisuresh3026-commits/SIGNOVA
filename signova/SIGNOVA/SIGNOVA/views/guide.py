import streamlit as st

from signova import ui
from signova.gestures import DYNAMIC_GESTURES, STATIC_GESTURES

ui.page_header("Supported gestures", "The complete vocabulary. Anything else is reported as Unknown.")


def gesture_cards(specs):
    return ui.grid(*[
        f'<div class="sg-card"><span class="ico">{s.emoji}</span><h4>{ui.esc(s.display)} &rarr; "{ui.esc(s.word)}"</h4>'
        f'<p>{ui.esc(s.how_to)}</p></div>' for s in specs.values()
    ])


st.markdown("### Hand poses (hold still for about 0.8 s)")
st.markdown(gesture_cards(STATIC_GESTURES), unsafe_allow_html=True)

st.markdown("### Hand motions (open palm, then move)")
st.markdown(gesture_cards(DYNAMIC_GESTURES), unsafe_allow_html=True)

st.markdown("### Tips for reliable results")
st.markdown(
    """
- Use good, even light on your hand and a plain background. Keep your hand roughly 30-60 cm from the camera.
- Face your palm to the camera for Open Palm, and keep your hand upright for Thumbs Up.
- Hold a pose steadily until the progress bar fills. Remove your hand or change the pose to add the same word again.
- For motions, rest the hand for a moment first, then make one clear sweep. Return your hand slowly or out of view, because a second movement right after the first is ignored for about a second.
- Swipe directions are as you see them on screen (the preview is mirrored like a mirror).
- If poses are often reported as Unknown, raise the light, move closer, or lower the strictness slider in the sidebar.
"""
)
st.markdown(
    '<div class="sg-note">The words are labels defined by this app (see <code>signova/gestures.py</code>). '
    'They are not official signs from any sign language, and you can change them in that file.</div>',
    unsafe_allow_html=True,
)
