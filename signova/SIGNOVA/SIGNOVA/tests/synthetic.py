"""Synthetic 21-point hands used to test the classifiers without a camera.

The geometry is a simplified, upright hand (wrist at the bottom, fingers up).
These landmarks are NOT real measurements - they verify the rule logic only.
"""
from __future__ import annotations

import numpy as np

# MCP knuckle positions (x, y) for index, middle, ring, pinky
MCP = {"index": (0.44, 0.66), "middle": (0.50, 0.65), "ring": (0.56, 0.66), "pinky": (0.62, 0.69)}
FINGER_IDX = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}

THUMB = {
    "out":   [(0.45, 0.80, 0), (0.40, 0.75, 0), (0.34, 0.70, 0), (0.27, 0.62, 0)],
    "up":    [(0.45, 0.80, 0), (0.42, 0.74, 0), (0.42, 0.65, 0), (0.42, 0.56, 0)],
    "tucked": [(0.45, 0.80, 0), (0.43, 0.75, 0), (0.49, 0.72, 0), (0.52, 0.69, 0)],
    "half":  [(0.45, 0.80, 0), (0.42, 0.75, 0), (0.45, 0.70, 0), (0.48, 0.66, 0)],
}


def make_hand(extended=(), thumb="tucked", dx=0.0, dy=0.0, rot90=False, aspect=1.0) -> np.ndarray:
    """Build a hand. `extended` lists raised fingers from {index, middle, ring, pinky}.

    The hand is designed in an isotropic space; `aspect` converts it to normalised
    image coordinates the way a real w:h frame would, so classifiers must undo it.
    """
    lm = np.zeros((21, 3))
    lm[0] = (0.5, 0.85, 0.0)
    for i, (x, y, z) in enumerate(THUMB[thumb], start=1):
        lm[i] = (x, y, z)
    for name, base in FINGER_IDX.items():
        x, y = MCP[name]
        if name in extended:
            lm[base] = (x, y, 0)
            lm[base + 1] = (x, y - 0.07, 0)
            lm[base + 2] = (x, y - 0.115, 0)
            lm[base + 3] = (x, y - 0.155, 0)
        else:
            lm[base] = (x, y, 0)
            lm[base + 1] = (x, y - 0.045, -0.03)
            lm[base + 2] = (x, y - 0.005, -0.06)
            lm[base + 3] = (x, y + 0.025, -0.04)
    lm[:, 0] += dx
    lm[:, 1] += dy
    if rot90:  # rotate 90 degrees clockwise on screen (y grows downward) around the wrist
        c = lm[0, :2].copy()
        rel = lm[:, :2] - c
        lm[:, 0] = c[0] - rel[:, 1]
        lm[:, 1] = c[1] + rel[:, 0]
    lm[:, 0] /= aspect
    lm[:, 2] /= aspect
    return lm


ALL4 = ("index", "middle", "ring", "pinky")

POSES = {
    "OPEN_PALM": dict(extended=ALL4, thumb="out"),
    "FIST": dict(extended=(), thumb="tucked"),
    "THUMBS_UP": dict(extended=(), thumb="up"),
    "ONE_FINGER": dict(extended=("index",), thumb="tucked"),
    "TWO_FINGERS": dict(extended=("index", "middle"), thumb="tucked"),
    "THREE_FINGERS": dict(extended=("index", "middle", "ring"), thumb="tucked"),
    "LOVE": dict(extended=("index", "pinky"), thumb="out"),
}
