"""Camera frame -> hand landmarks -> gesture -> word pipeline (no Streamlit code here)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

import cv2
import numpy as np

from . import overlay
from .config import Settings
from .features import hand_orientation, palm_center, to_metric
from .gestures import (ALL_GESTURES, STATIC_GESTURES, UNKNOWN, GestureResult,
                       classify_hand)
from .hand_tracker import HandObservation, HandTracker
from .motion import DynamicEvent, MotionState, MotionTracker
from .stabilizer import HoldConfirmer


@dataclass
class HandInfo:
    obs: HandObservation
    gesture: GestureResult
    orientation_deg: float
    orientation_label: str


@dataclass
class Commit:
    key: str
    word: str
    source: str       # "static" or "dynamic"
    quality: float


@dataclass
class FrameResult:
    t: float = 0.0
    frame_rgb: Optional[np.ndarray] = None
    hands: List[HandInfo] = field(default_factory=list)
    primary: Optional[HandInfo] = None
    motion: MotionState = field(default_factory=MotionState)
    hold_progress: float = 0.0
    latched: bool = False
    commit: Optional[Commit] = None
    dynamic_event: Optional[DynamicEvent] = None
    fps: float = 0.0

    @property
    def hand_count(self) -> int:
        return len(self.hands)


class SignovaPipeline:
    def __init__(self, settings: Settings, tracker: Optional[HandTracker] = None):
        self.settings = settings
        self.tracker = tracker
        self.motion = MotionTracker()
        self.confirmer = HoldConfirmer(hold_s=settings.hold_seconds)
        self._primary_label: Optional[str] = None
        self._fps = 0.0
        self._last_t: Optional[float] = None
        self._banner: Optional[str] = None
        self._banner_until = 0.0

    # ------------------------------------------------------------- settings
    def configure(self, settings: Settings) -> None:
        self.settings = settings
        self.confirmer.hold_s = settings.hold_seconds

    # ------------------------------------------------------- core (testable)
    def process_observations(self, t: float, observations: List[HandObservation], aspect: float) -> FrameResult:
        result = FrameResult(t=t)
        for obs in observations:
            g = classify_hand(obs.landmarks, aspect, self.settings.min_quality)
            ang, label = hand_orientation(to_metric(obs.landmarks, aspect))
            result.hands.append(HandInfo(obs, g, ang, label))
        result.primary = self._choose_primary(result.hands)

        primary = result.primary
        if primary is None:
            result.motion = self.motion.update(t, None)
            out = self.confirmer.update(t, None, 0.0)
        else:
            open_palm = primary.gesture.key == "OPEN_PALM"
            result.motion = self.motion.update(t, palm_center(primary.obs.landmarks), aspect, open_palm)
            event = self.motion.detect(t)
            if event:
                spec = ALL_GESTURES[event.key]
                result.dynamic_event = event
                result.commit = Commit(event.key, spec.word, "dynamic", event.confidence)
                self.confirmer.latch(primary.gesture.key if primary.gesture.is_known else None)
                self._banner, self._banner_until = f"{spec.display}: {spec.word}", t + 1.2
                out = self.confirmer.update(t, primary.gesture.key, result.motion.speed)
            else:
                out = self.confirmer.update(t, primary.gesture.key, result.motion.speed)
                if out.committed:
                    spec = STATIC_GESTURES[out.committed]
                    result.commit = Commit(out.committed, spec.word, "static", primary.gesture.quality)
        result.hold_progress, result.latched = out.progress, out.latched
        return result

    def _choose_primary(self, hands: List[HandInfo]) -> Optional[HandInfo]:
        if not hands:
            self._primary_label = None
            return None
        if self._primary_label:
            for h in hands:
                if h.obs.handedness == self._primary_label:
                    return h
        best = max(hands, key=lambda h: h.obs.score)
        self._primary_label = best.obs.handedness
        return best

    # ------------------------------------------------------- full frame path
    def process_frame(self, frame_bgr: np.ndarray, t: Optional[float] = None) -> FrameResult:
        if self.tracker is None:
            raise RuntimeError("No hand tracker attached to the pipeline.")
        t = time.monotonic() if t is None else t
        frame = cv2.flip(frame_bgr, 1) if self.settings.mirror else frame_bgr.copy()
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        observations = self.tracker.detect(rgb)
        if not self.settings.mirror:  # MediaPipe assumes a mirrored (selfie) image for Left/Right
            for o in observations:
                o.handedness = {"Left": "Right", "Right": "Left"}.get(o.handedness, o.handedness)
        result = self.process_observations(t, observations, w / float(h))

        for info in result.hands:
            overlay.draw_hand(frame, info.obs.landmarks, self.settings.show_indices)
            x0, y0, x1, y1 = overlay.hand_box(frame, info.obs.landmarks)
            is_primary = info is result.primary
            cv2.rectangle(frame, (x0, y0), (x1, y1), overlay.PURPLE if is_primary else overlay.LAVENDER, 1)
            g = info.gesture
            text = f"{info.obs.handedness}: {g.display}" + (f" {g.quality:.0%}" if g.is_known else "")
            overlay.draw_label(frame, text, (x0, y0 - 4), overlay.PURPLE if g.is_known else (110, 90, 90))
        if result.primary is not None:
            overlay.draw_hold_bar(frame, result.hold_progress, result.latched)
        if self._banner and t < self._banner_until:
            overlay.draw_banner(frame, self._banner)

        if self._last_t is not None and t > self._last_t:
            inst = 1.0 / (t - self._last_t)
            self._fps = inst if self._fps == 0 else 0.9 * self._fps + 0.1 * inst
        self._last_t = t
        result.fps = self._fps
        cv2.putText(frame, f"{self._fps:4.1f} fps", (10, h - 30), overlay.FONT, 0.45, overlay.LAVENDER, 1, cv2.LINE_AA)
        result.frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return result

    def close(self) -> None:
        if self.tracker is not None:
            self.tracker.close()
            self.tracker = None
