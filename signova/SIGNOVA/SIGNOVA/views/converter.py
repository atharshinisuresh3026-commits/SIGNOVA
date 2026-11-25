import json
import time

import streamlit as st
import streamlit.components.v1 as components

from signova import ui
from signova.gestures import ALL_GESTURES, DYNAMIC_GESTURES, STATIC_GESTURES
from signova.overlay import placeholder_frame
from signova.state import bump_text, current_settings, get_db, init_state, start_camera, stop_camera

init_state()
ss = st.session_state

# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### Converter settings")
    st.selectbox("Camera number", [0, 1, 2, 3], key="set_camera", disabled=ss.running,
                 help="0 is the default webcam. Try 1 or 2 for an external camera. Stop the camera to change it.")
    st.radio("Hands to track", [1, 2], key="set_hands", horizontal=True, disabled=ss.running,
             help="With two hands both are drawn, but only the primary hand adds words.")
    st.toggle("Mirror preview", value=True, key="set_mirror")
    st.slider("Hold time to add a word (seconds)", 0.4, 2.0, 0.8, 0.1, key="set_hold",
              help="How long a pose must be held steadily before its word is added.")
    st.slider("Recognition strictness", 0.2, 0.8, 0.40, 0.05, key="set_quality",
              help="Higher values report more poses as Unknown instead of guessing.")
    st.toggle("Show landmark numbers", key="set_indices")
    st.toggle("Show debug values", key="set_debug")


# ------------------------------------------------------------- live fragment
def apply_commit(commit) -> None:
    ss.buffer.add(commit.word)
    bump_text()
    ss.events.insert(0, {"word": commit.word, "label": ALL_GESTURES[commit.key].display,
                         "source": commit.source, "time": time.strftime("%H:%M:%S")})
    del ss.events[8:]
    st.toast(f"Added \"{commit.word}\"", icon="✅")


def recognition_panel(result) -> None:
    if not ss.running:
        st.markdown('<div class="sg-gesture unknown"><div class="name">Waiting for camera</div>'
                    '<div class="word">Press Start camera, then hold a gesture from the guide below.</div></div>',
                    unsafe_allow_html=True)
    elif result is None or result.primary is None:
        st.markdown('<div class="sg-gesture unknown"><div class="name">No hand detected</div>'
                    '<div class="word">Raise one hand into view with good lighting.</div></div>'
                    + ui.meter(0), unsafe_allow_html=True)
    else:
        p, g = result.primary, result.primary.gesture
        if g.is_known:
            head = (f'<div class="sg-gesture"><div class="name">{ui.esc(g.display)}</div>'
                    f'<div class="word">Adds the word "{ui.esc(g.word)}"</div></div>')
        else:
            head = (f'<div class="sg-gesture unknown"><div class="name">Unknown gesture</div>'
                    f'<div class="word">{ui.esc(g.reason or "Not in the supported vocabulary.")}</div></div>')
        st.markdown(head, unsafe_allow_html=True)

        st.markdown(f'<div class="sg-cap">Match quality (heuristic, not accuracy): {g.quality:.0%}</div>'
                    + ui.meter(g.quality if g.is_known else 0), unsafe_allow_html=True)

        if result.latched:
            hold_text, css = "Added. Release or change the pose to add it again.", "done"
        elif result.motion.moving and g.is_known:
            hold_text, css = "Hand is moving. Hold still to add this pose.", "hold"
        elif g.is_known:
            hold_text, css = f"Hold steady to add: {result.hold_progress:.0%}", "hold"
        else:
            hold_text, css = "Show a supported gesture.", "hold"
        st.markdown(f'<div class="sg-cap">{ui.esc(hold_text)}</div>'
                    + ui.meter(1.0 if result.latched else result.hold_progress, css), unsafe_allow_html=True)

        st.markdown(ui.finger_chips({k.capitalize(): v for k, v in g.fingers.items()}), unsafe_allow_html=True)
        m = result.motion
        st.markdown(ui.kv({
            "Hand": p.obs.handedness,
            "Pointing": f"{p.orientation_label} ({p.orientation_deg:.0f} deg)",
            "Movement": m.direction if m.moving else "Still",
            "Speed": f"{m.speed:.2f} heights/s",
        }), unsafe_allow_html=True)
        if ss.get("set_debug"):
            st.markdown(ui.kv({f"{k} extension": f"{v:.2f}" for k, v in g.extension.items()}
                              | {"Thumb up score": f"{g.thumb_up:.2f}"}), unsafe_allow_html=True)

    if result is not None and result.dynamic_event is not None:
        e = result.dynamic_event
        st.success(f"Motion recognised: {ALL_GESTURES[e.key].display}")
    if ss.events:
        st.markdown("**Recently added**")
        st.markdown("".join(
            f'<div class="sg-recent">{ui.esc(ev["word"])} <small>{ui.esc(ev["label"])}, {ui.esc(ev["time"])}</small></div>'
            for ev in ss.events[:5]), unsafe_allow_html=True)


def live_panel() -> None:
    result, failure = None, ""
    if ss.running and ss.pipeline is not None and ss.camera is not None:
        cam, pipe = ss.camera, ss.pipeline
        pipe.configure(current_settings())
        if cam.error:
            failure = cam.error
        else:
            frame, frame_id = cam.read()
            if frame is not None and frame_id != ss.last_frame_id:
                ss.last_frame_id = frame_id
                try:
                    result = pipe.process_frame(frame)
                    ss.last_result = result
                except Exception as exc:  # keep the app alive and explain what happened
                    failure = f"Frame processing failed: {exc}"
            else:
                result = ss.last_result
    if failure:
        stop_camera()
        ss.camera_error = failure
        st.rerun(scope="app")
    if result is not None and result.commit is not None:
        apply_commit(result.commit)
        ss.last_result.commit = None
        st.rerun(scope="app")

    left, right = st.columns([3, 2], gap="large")
    with left:
        if result is not None and result.frame_rgb is not None:
            ui.show_image(result.frame_rgb)
        elif ss.running:
            ui.show_image(placeholder_frame("Starting camera", "Waiting for the first frame"))
        else:
            ui.show_image(placeholder_frame("Camera is off", "Press Start camera to begin"))
        if ss.running:
            n = result.hand_count if result else 0
            st.markdown(ui.badges(
                ui.badge("Camera live", "ok"),
                ui.badge(f"{n} hand{'s' if n != 1 else ''} detected" if n else "No hand detected", "ok" if n else "warn"),
                ui.badge(f"{result.fps:.0f} fps" if result and result.fps else "measuring speed", "off"),
            ), unsafe_allow_html=True)
        else:
            st.markdown(ui.badges(ui.badge("Camera off", "off"), ui.badge("Hand tracking idle", "off")),
                        unsafe_allow_html=True)
    with right:
        recognition_panel(result)


# --------------------------------------------------------------------- page
ui.page_header("Converter", "Hold a gesture to the camera. Video is processed on this computer and never stored.")

c_start, c_stop, c_status = st.columns([1.2, 1.2, 3])
if c_start.button("Start camera", type="primary", disabled=ss.running, key="btn_start"):
    with st.spinner("Starting the camera and loading the hand-tracking model..."):
        error = start_camera()
    ss.camera_error = error or ""
    st.rerun()
if c_stop.button("Stop camera", disabled=not ss.running, key="btn_stop_cam"):
    stop_camera()
    st.rerun()
if ss.camera_error:
    c_status.markdown(ui.badges(ui.badge("Camera error", "err")), unsafe_allow_html=True)
    st.error(ss.camera_error, icon="🚫")

st.fragment(run_every=0.07 if ss.running else None)(live_panel)()

# ------------------------------------------------------------ sentence builder
st.markdown("### Sentence")
buf = ss.buffer


def on_edit() -> None:
    ss.buffer.set_text(ss.get(f"sentence_{ss.text_version}", ""))


def cb_delete() -> None:
    if ss.buffer.delete_last():
        bump_text()
    else:
        ss.flash = ("warning", "There are no words to delete.")


def cb_clear() -> None:
    if len(ss.buffer):
        ss.buffer.clear()
        bump_text()
    else:
        ss.flash = ("info", "The text is already empty.")


def cb_save() -> None:
    text = ss.buffer.text
    if not text:
        ss.flash = ("warning", "Nothing to save yet. Add words first.")
        return
    try:
        get_db().add(text)
        ss.flash = ("success", "Saved to history.")
    except Exception as exc:
        ss.flash = ("error", f"Could not save: {exc}")


st.text_area("Converted text (you can edit it directly)", value=buf.text, key=f"sentence_{ss.text_version}",
             height=130, on_change=on_edit, placeholder="Recognised words appear here...")
b1, b2, b3, b4 = st.columns([1, 1, 1, 2])
b1.button("Delete last word", on_click=cb_delete, key="btn_del_word")
b2.button("Clear text", on_click=cb_clear, key="btn_clear")
b3.button("Save to history", on_click=cb_save, key="btn_save", type="primary")
b4.caption(f"{len(buf)} word(s)")
if ss.flash:
    kind, message = ss.flash
    ss.flash = None
    getattr(st, kind)(message)

# ------------------------------------------------------------------ speech
st.markdown("### Read aloud")
tts = ss.tts
s1, s2, s3, s4 = st.columns([1, 1, 2, 2])
rate = s3.slider("Speech speed", 100, 260, 170, 10, key="tts_rate")
volume = s4.slider("Volume", 0.0, 1.0, 1.0, 0.1, key="tts_volume")
if s1.button("Speak", key="btn_speak", type="primary"):
    ok, message = tts.speak(buf.text, rate, volume)
    (st.success if ok else st.warning)(message)
if s2.button("Stop speaking", key="btn_stop_speak"):
    tts.stop()
    st.info("Speech stopped.")
if not tts.engine_installed():
    st.caption("System voice (pyttsx3) is not installed, so use the browser voice below.")

text_js = json.dumps(buf.text).replace("</", "<\\/")
components.html(
    '<div style="font-family:Segoe UI,Arial,sans-serif;display:flex;gap:10px;align-items:center;flex-wrap:wrap">'
    '<button id="sp" style="background:#2a1f5c;color:#fff;border:1px solid #8B5CF6;border-radius:10px;padding:8px 16px;cursor:pointer">Speak in browser</button>'
    '<button id="st" style="background:#14142A;color:#C4B5FD;border:1px solid #2A2547;border-radius:10px;padding:8px 16px;cursor:pointer">Stop</button>'
    '<span id="msg" style="color:#a9a3c7;font-size:14px"></span></div>'
    "<script>const text=" + text_js + ";const rate=" + str(round(rate / 170, 2)) + ";const vol=" + str(volume) + ";"
    "const synth=window.speechSynthesis;const msg=document.getElementById('msg');"
    "if(!synth){msg.textContent='This browser does not support speech.';}"
    "document.getElementById('sp').onclick=()=>{if(!synth){return;}"
    "if(!text.trim()){msg.textContent='There is no text to read yet.';return;}"
    "synth.cancel();const u=new SpeechSynthesisUtterance(text);u.rate=rate;u.volume=vol;"
    "u.onend=()=>{msg.textContent='';};synth.speak(u);msg.textContent='Speaking...';};"
    "document.getElementById('st').onclick=()=>{if(synth){synth.cancel();}msg.textContent='';};</script>",
    height=60,
)

# ------------------------------------------------------------------ guide
with st.expander("Supported gestures", expanded=False):
    rows = ["| Gesture | Word | How to make it |", "|---|---|---|"]
    for spec in list(STATIC_GESTURES.values()) + list(DYNAMIC_GESTURES.values()):
        rows.append(f"| {spec.emoji} {spec.display} | {spec.word} | {spec.how_to} |")
    st.markdown("\n".join(rows))
    st.caption("Poses are added after a steady hold. Motions use an open palm. Anything else shows as Unknown.")
