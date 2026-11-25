"""Streamlit session-state helpers: camera lifecycle, settings and shared objects."""
from __future__ import annotations

import atexit
from typing import Optional

import streamlit as st

from .camera import Camera, CameraError
from .config import Settings
from .database import HistoryDB
from .hand_tracker import HandTracker, MediaPipeUnavailable
from .pipeline import SignovaPipeline
from .text_buffer import TextBuffer
from .tts import TextToSpeech

_open_cameras: list = []


@atexit.register
def _release_all() -> None:  # last-resort cleanup when the server process exits
    for cam in list(_open_cameras):
        try:
            cam.release()
        except Exception:
            pass


@st.cache_resource
def get_db() -> HistoryDB:
    return HistoryDB()


def init_state() -> None:
    ss = st.session_state
    defaults = {
        "camera": None, "pipeline": None, "running": False, "camera_error": "",
        "buffer": TextBuffer(), "text_version": 0, "last_result": None, "last_frame_id": -1,
        "events": [], "flash": None, "tts": TextToSpeech(), "read_failures": 0,
    }
    for key, value in defaults.items():
        ss.setdefault(key, value)


def bump_text() -> None:
    """Force the text box to be rebuilt from the buffer (new widget key)."""
    st.session_state.text_version += 1


def current_settings() -> Settings:
    ss = st.session_state
    return Settings(
        camera_index=int(ss.get("set_camera", 0)),
        mirror=bool(ss.get("set_mirror", True)),
        max_hands=int(ss.get("set_hands", 1)),
        hold_seconds=float(ss.get("set_hold", 0.8)),
        min_quality=float(ss.get("set_quality", 0.40)),
        show_indices=bool(ss.get("set_indices", False)),
    )


def start_camera() -> Optional[str]:
    """Open the webcam and hand tracker. Returns an error message, or None on success."""
    ss = st.session_state
    stop_camera()
    settings = current_settings()
    cam = Camera(settings.camera_index, settings.frame_width, settings.frame_height)
    try:
        tracker = HandTracker(settings.max_hands, settings.model_complexity,
                              settings.min_detection_confidence, settings.min_tracking_confidence)
    except MediaPipeUnavailable as exc:
        return str(exc)
    except Exception as exc:
        return f"Hand-tracking model failed to start: {exc}"
    try:
        cam.open()
    except CameraError as exc:
        tracker.close()
        return str(exc)
    except Exception as exc:
        tracker.close()
        cam.release()
        return f"Unexpected camera error: {exc}"
    _open_cameras.append(cam)
    ss.camera, ss.pipeline = cam, SignovaPipeline(settings, tracker)
    ss.running, ss.camera_error, ss.last_result, ss.last_frame_id, ss.read_failures = True, "", None, -1, 0
    return None


def stop_camera() -> None:
    """Release the webcam and the tracker. Safe to call at any time."""
    ss = st.session_state
    cam: Optional[Camera] = ss.get("camera")
    if cam is not None:
        cam.release()
        if cam in _open_cameras:
            _open_cameras.remove(cam)
    pipe: Optional[SignovaPipeline] = ss.get("pipeline")
    if pipe is not None:
        pipe.close()
    ss.camera, ss.pipeline, ss.running, ss.last_result = None, None, False, None
