"""Drawing helpers: purple hand skeleton and heads-up display on the video frame (BGR)."""
from __future__ import annotations

import cv2
import numpy as np

from .features import FINGERTIPS, HAND_CONNECTIONS

PURPLE = (246, 92, 139)      # #8B5CF6 in BGR
LAVENDER = (253, 181, 196)   # #C4B5FD
WHITE = (245, 245, 245)
DARK = (20, 11, 11)
GREEN = (120, 220, 130)
AMBER = (60, 190, 245)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_hand(img: np.ndarray, landmarks: np.ndarray, show_indices: bool = False) -> None:
    h, w = img.shape[:2]
    pts = [(int(x * w), int(y * h)) for x, y, _ in landmarks]
    for a, b in HAND_CONNECTIONS:
        cv2.line(img, pts[a], pts[b], LAVENDER, 2, cv2.LINE_AA)
    for i, p in enumerate(pts):
        tip = i in FINGERTIPS
        cv2.circle(img, p, 6 if tip else 4, PURPLE, -1, cv2.LINE_AA)
        cv2.circle(img, p, 7 if tip else 5, WHITE, 1, cv2.LINE_AA)
        if show_indices:
            cv2.putText(img, str(i), (p[0] + 6, p[1] - 6), FONT, 0.4, WHITE, 1, cv2.LINE_AA)


def hand_box(img: np.ndarray, landmarks: np.ndarray, pad: int = 14):
    h, w = img.shape[:2]
    xs, ys = landmarks[:, 0] * w, landmarks[:, 1] * h
    x0, y0 = max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad)
    x1, y1 = min(w - 1, int(xs.max()) + pad), min(h - 1, int(ys.max()) + pad)
    return x0, y0, x1, y1


def draw_label(img: np.ndarray, text: str, org, color=PURPLE, scale: float = 0.6) -> None:
    (tw, th), base = cv2.getTextSize(text, FONT, scale, 2)
    x, y = org
    x = max(0, min(x, img.shape[1] - tw - 10))
    y = max(th + 8, y)
    cv2.rectangle(img, (x, y - th - 8), (x + tw + 10, y + base - 2), color, -1)
    cv2.putText(img, text, (x + 5, y - 4), FONT, scale, WHITE, 2, cv2.LINE_AA)


def draw_hold_bar(img: np.ndarray, progress: float, latched: bool) -> None:
    h, w = img.shape[:2]
    x0, x1, y0, y1 = 16, w - 16, h - 22, h - 12
    cv2.rectangle(img, (x0, y0), (x1, y1), (60, 40, 45), -1)
    fill = int((x1 - x0) * max(0.0, min(1.0, progress)))
    if fill > 0:
        cv2.rectangle(img, (x0, y0), (x0 + fill, y1), GREEN if latched else PURPLE, -1)


def draw_banner(img: np.ndarray, text: str) -> None:
    h, w = img.shape[:2]
    (tw, th), _ = cv2.getTextSize(text, FONT, 0.9, 2)
    x = (w - tw) // 2
    cv2.rectangle(img, (x - 14, 14), (x + tw + 14, 24 + th + 12), PURPLE, -1)
    cv2.putText(img, text, (x, 24 + th + 2), FONT, 0.9, WHITE, 2, cv2.LINE_AA)


def placeholder_frame(title: str, subtitle: str = "", w: int = 640, h: int = 480) -> np.ndarray:
    """RGB image shown when the camera is off, so the layout does not jump around."""
    img = np.full((h, w, 3), (20, 11, 11), dtype=np.uint8)  # BGR of #0B0B14
    cv2.rectangle(img, (1, 1), (w - 2, h - 2), (70, 40, 60), 1)
    for text, y, scale, color in ((title, h // 2 - 8, 0.9, LAVENDER), (subtitle, h // 2 + 28, 0.55, (170, 150, 150))):
        (tw, _), _ = cv2.getTextSize(text, FONT, scale, 2 if scale > 0.8 else 1)
        cv2.putText(img, text, ((w - tw) // 2, y), FONT, scale, color, 2 if scale > 0.8 else 1, cv2.LINE_AA)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
