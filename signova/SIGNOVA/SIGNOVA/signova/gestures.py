"""Static gesture vocabulary and landmark-based classifier.

IMPORTANT: this is an app-defined gesture vocabulary, NOT a sign-language
translator. Each supported hand pose is mapped to a word chosen by this project.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np

from .features import (FINGER_NAMES, clip01, extension_scores, thumb_up_score,
                       to_metric)

UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class GestureSpec:
    key: str
    display: str
    word: str
    how_to: str
    kind: str  # "static" or "dynamic"
    emoji: str = ""


STATIC_GESTURES: Dict[str, GestureSpec] = {
    "OPEN_PALM": GestureSpec("OPEN_PALM", "Open Palm", "Hello",
                             "All four fingers straight and spread, palm toward the camera.", "static", "✋"),
    "FIST": GestureSpec("FIST", "Closed Fist", "Stop",
                        "All fingers curled into the palm, thumb tucked in.", "static", "✊"),
    "THUMBS_UP": GestureSpec("THUMBS_UP", "Thumbs Up", "Yes",
                             "Fingers curled, thumb pointing straight up (keep the hand upright).", "static", "👍"),
    "ONE_FINGER": GestureSpec("ONE_FINGER", "One Finger", "One",
                              "Only the index finger raised; other fingers and thumb tucked.", "static", "☝️"),
    "TWO_FINGERS": GestureSpec("TWO_FINGERS", "Two Fingers", "Two",
                               "Index and middle fingers raised; ring, pinky and thumb tucked.", "static", "✌️"),
    "THREE_FINGERS": GestureSpec("THREE_FINGERS", "Three Fingers", "Three",
                                 "Index, middle and ring fingers raised; pinky and thumb tucked.", "static", "3️⃣"),
    "LOVE": GestureSpec("LOVE", "Love Sign", "Love",
                        "Thumb, index finger and pinky raised; middle and ring fingers curled.", "static", "🤟"),
}

DYNAMIC_GESTURES: Dict[str, GestureSpec] = {
    "WAVE": GestureSpec("WAVE", "Wave", "Goodbye",
                        "Open palm, wave side to side at least 3 times.", "dynamic", "👋"),
    "SWIPE_RIGHT": GestureSpec("SWIPE_RIGHT", "Swipe Right", "Go",
                               "Open palm, one quick sweep toward the right of the screen.", "dynamic", "➡️"),
    "SWIPE_LEFT": GestureSpec("SWIPE_LEFT", "Swipe Left", "No",
                              "Open palm, one quick sweep toward the left of the screen.", "dynamic", "⬅️"),
    "SWIPE_UP": GestureSpec("SWIPE_UP", "Swipe Up", "Please",
                            "Open palm, one quick upward sweep.", "dynamic", "⬆️"),
    "SWIPE_DOWN": GestureSpec("SWIPE_DOWN", "Swipe Down", "Thank you",
                              "Open palm, one quick downward sweep.", "dynamic", "⬇️"),
}

ALL_GESTURES: Dict[str, GestureSpec] = {**STATIC_GESTURES, **DYNAMIC_GESTURES}


@dataclass
class GestureResult:
    key: str = UNKNOWN
    quality: float = 0.0            # heuristic 0..1 match quality, NOT a probability
    fingers: Dict[str, bool] = field(default_factory=dict)
    extension: Dict[str, float] = field(default_factory=dict)
    thumb_up: float = 0.0
    reason: str = ""

    @property
    def is_known(self) -> bool:
        return self.key in STATIC_GESTURES

    @property
    def display(self) -> str:
        return STATIC_GESTURES[self.key].display if self.is_known else "Unknown"

    @property
    def word(self) -> str:
        return STATIC_GESTURES[self.key].word if self.is_known else ""


def _decisive(e: float) -> float:
    """1 when a finger is clearly extended/curled, 0 when it sits on the threshold."""
    return abs(2.0 * clip01(e) - 1.0)


def classify_hand(landmarks: np.ndarray, aspect: float = 1.0, min_quality: float = 0.40,
                  thumb_up_min: float = 0.80) -> GestureResult:
    """Classify one hand from 21 landmarks using finger-state rules."""
    pts = to_metric(landmarks, aspect)
    ext = extension_scores(pts)
    up = thumb_up_score(pts)
    state = {n: ext[n] >= 0.5 for n in FINGER_NAMES}
    thumb, index, middle, ring, pinky = (state[n] for n in FINGER_NAMES)
    four = [index, middle, ring, pinky]

    key = UNKNOWN
    considered = list(FINGER_NAMES)
    if all(four):
        key, considered = "OPEN_PALM", ["index", "middle", "ring", "pinky"]
    elif thumb and not any(four) and up >= thumb_up_min:
        key = "THUMBS_UP"
    elif thumb and index and pinky and not middle and not ring:
        key = "LOVE"
    elif not thumb and not any(four):
        key = "FIST"
    elif not thumb and index and not middle and not ring and not pinky:
        key = "ONE_FINGER"
    elif not thumb and index and middle and not ring and not pinky:
        key = "TWO_FINGERS"
    elif not thumb and index and middle and ring and not pinky:
        key = "THREE_FINGERS"

    if key == UNKNOWN:
        return GestureResult(UNKNOWN, 0.0, state, ext, up,
                             "Hand pose does not match a supported gesture.")

    quality = float(np.mean([_decisive(ext[n]) for n in considered]))
    if key == "THUMBS_UP":
        quality = 0.75 * quality + 0.25 * clip01((up - 0.6) / 0.4)
    if quality < min_quality:
        return GestureResult(UNKNOWN, quality, state, ext, up,
                             f"Pose looks like {STATIC_GESTURES[key].display} but is too uncertain "
                             f"({quality:.0%}). Hold the hand clearly and steadily.")
    return GestureResult(key, quality, state, ext, up, "")
