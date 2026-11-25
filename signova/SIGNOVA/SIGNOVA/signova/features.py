"""Geometry helpers: finger extension, hand orientation and landmark constants.

All functions work on a (21, 3) NumPy array of MediaPipe-style hand landmarks
(x and y normalised to 0..1, z relative depth). Before measuring, coordinates are
scaled to an isotropic space (x * aspect, y, z * aspect) so angles and distances
are not distorted by a 4:3 or 16:9 frame.
"""
from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np

WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, MIDDLE_MCP, PINKY_MCP = 5, 9, 17
FINGERTIPS = (4, 8, 12, 16, 20)
PALM_POINTS = (0, 5, 9, 13, 17)

FINGER_NAMES = ("thumb", "index", "middle", "ring", "pinky")
FINGER_JOINTS: Dict[str, Tuple[int, int, int, int]] = {
    "index": (5, 6, 7, 8),
    "middle": (9, 10, 11, 12),
    "ring": (13, 14, 15, 16),
    "pinky": (17, 18, 19, 20),
}

HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
)

EPS = 1e-6


def to_metric(landmarks: np.ndarray, aspect: float = 1.0) -> np.ndarray:
    """Return landmarks scaled into an isotropic coordinate system."""
    pts = np.asarray(landmarks, dtype=float)
    if pts.shape != (21, 3):
        raise ValueError(f"expected landmarks of shape (21, 3), got {pts.shape}")
    return pts * np.array([aspect, 1.0, aspect])


def dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def angle_deg(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at point b (degrees) formed by a-b-c. 180 means a straight line."""
    v1, v2 = a - b, c - b
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < EPS or n2 < EPS:
        return 0.0
    cos = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
    return math.degrees(math.acos(cos))


def clip01(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


def palm_size(pts: np.ndarray) -> float:
    return max(dist(pts[WRIST], pts[MIDDLE_MCP]), EPS)


def finger_extension(pts: np.ndarray, name: str) -> float:
    """Extension score 0 (fully curled) .. 1 (fully straight) for a non-thumb finger.

    Combines two independent cues: how straight the PIP/DIP joints are and how far
    the fingertip is from the wrist compared with the knuckle (MCP).
    """
    mcp, pip, dip, tip = FINGER_JOINTS[name]
    straightness = (angle_deg(pts[mcp], pts[pip], pts[dip]) + angle_deg(pts[pip], pts[dip], pts[tip])) / 2.0
    e_angle = clip01((straightness - 120.0) / (165.0 - 120.0))
    ratio = dist(pts[tip], pts[WRIST]) / max(dist(pts[mcp], pts[WRIST]), EPS)
    e_reach = clip01((ratio - 1.25) / (1.75 - 1.25))
    return 0.5 * e_angle + 0.5 * e_reach


def thumb_extension(pts: np.ndarray) -> float:
    """Extension score for the thumb (0 tucked .. 1 stretched away from the palm)."""
    ip_angle = angle_deg(pts[THUMB_MCP], pts[THUMB_IP], pts[THUMB_TIP])
    # Distance from the thumb tip to the pinky knuckle: small when the thumb is tucked
    # across the palm, large when it points away (sideways or up).
    reach = dist(pts[THUMB_TIP], pts[PINKY_MCP]) / palm_size(pts)
    e_angle = clip01((ip_angle - 140.0) / (170.0 - 140.0))
    e_reach = clip01((reach - 0.65) / (1.05 - 0.65))
    return 0.25 * e_angle + 0.75 * e_reach


def thumb_up_score(pts: np.ndarray) -> float:
    """How vertical the thumb is on screen (1 = straight up, <=0 = sideways/down)."""
    v = pts[THUMB_TIP][:2] - pts[THUMB_MCP][:2]
    n = np.linalg.norm(v)
    if n < EPS:
        return 0.0
    return float(-v[1] / n)  # image y grows downward


def extension_scores(pts: np.ndarray) -> Dict[str, float]:
    scores = {"thumb": thumb_extension(pts)}
    for name in FINGER_JOINTS:
        scores[name] = finger_extension(pts, name)
    return scores


def hand_orientation(pts: np.ndarray) -> Tuple[float, str]:
    """Direction the hand points on screen: wrist -> middle knuckle.

    Returns (angle in degrees, label). 0 = right, 90 = up, 180 = left, -90 = down.
    """
    v = pts[MIDDLE_MCP][:2] - pts[WRIST][:2]
    ang = math.degrees(math.atan2(-v[1], v[0]))
    if 45 <= ang < 135:
        label = "Up"
    elif -135 <= ang < -45:
        label = "Down"
    elif -45 <= ang < 45:
        label = "Right"
    else:
        label = "Left"
    return ang, label


def palm_center(landmarks: np.ndarray) -> Tuple[float, float]:
    """Centre of the palm in normalised image coordinates (x, y)."""
    p = np.asarray(landmarks, dtype=float)[list(PALM_POINTS)]
    return float(p[:, 0].mean()), float(p[:, 1].mean())
