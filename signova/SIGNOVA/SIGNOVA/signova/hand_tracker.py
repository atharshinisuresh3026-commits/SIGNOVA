"""MediaPipe Hands wrapper (all processing is local; nothing is sent anywhere)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


class MediaPipeUnavailable(RuntimeError):
    """MediaPipe is missing or is a build without the classic Hands solution."""


@dataclass
class HandObservation:
    landmarks: np.ndarray   # (21, 3) normalised x, y and relative z
    handedness: str         # "Left" / "Right" as seen after mirroring
    score: float            # MediaPipe handedness score


class HandTracker:
    def __init__(self, max_hands: int = 1, model_complexity: int = 1,
                 min_detection_confidence: float = 0.6, min_tracking_confidence: float = 0.5):
        try:
            import mediapipe as mp
        except Exception as exc:  # ImportError or a broken native install
            raise MediaPipeUnavailable(
                "MediaPipe could not be imported. Install the pinned version with "
                "'pip install -r requirements.txt' (Python 3.9-3.12). Details: " + str(exc)
            ) from exc
        solutions = getattr(mp, "solutions", None)
        if solutions is None or not hasattr(solutions, "hands"):
            raise MediaPipeUnavailable(
                f"This MediaPipe build ({getattr(mp, '__version__', 'unknown')}) no longer ships the classic "
                "'solutions.hands' API that SIGNOVA uses. Install the tested version: "
                "pip install \"mediapipe>=0.10.14,<0.10.22\""
            )
        self._hands = solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.max_hands = max_hands

    def detect(self, frame_rgb: np.ndarray) -> List[HandObservation]:
        frame_rgb.flags.writeable = False
        result = self._hands.process(frame_rgb)
        frame_rgb.flags.writeable = True
        hands: List[HandObservation] = []
        if not result.multi_hand_landmarks:
            return hands
        infos = result.multi_handedness or []
        for i, lm in enumerate(result.multi_hand_landmarks):
            arr = np.array([[p.x, p.y, p.z] for p in lm.landmark], dtype=float)
            label, score = "Hand", 0.0
            if i < len(infos) and infos[i].classification:
                label = infos[i].classification[0].label
                score = float(infos[i].classification[0].score)
            hands.append(HandObservation(arr, label, score))
        return hands

    def close(self) -> None:
        try:
            self._hands.close()
        except Exception:
            pass
