"""Dynamic (motion) gesture recognition from palm-centre trajectories.

Supported: WAVE and SWIPE_LEFT/RIGHT/UP/DOWN, always performed with an open palm.
Coordinates are converted to "frame-height units" so a 4:3 / 16:9 frame does not
bias horizontal versus vertical movement. Directions are as seen on screen.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Tuple


@dataclass
class MotionState:
    speed: float = 0.0        # frame-heights per second (recent window)
    dx: float = 0.0           # recent displacement, right is positive
    dy: float = 0.0           # recent displacement, down is positive
    distance: float = 0.0     # path length in the recent window
    direction: str = "Still"  # Left / Right / Up / Down / Still
    moving: bool = False


@dataclass
class DynamicEvent:
    key: str
    confidence: float
    detail: str
    t: float


def count_reversals(xs: List[float], amp: float) -> int:
    """Count direction reversals whose swing is at least `amp`."""
    if len(xs) < 2:
        return 0
    ref, direction, reversals = xs[0], 0, 0
    for x in xs[1:]:
        if direction == 0:
            if abs(x - ref) >= amp:
                direction, ref = (1 if x > ref else -1), x
        elif direction == 1:
            if x > ref:
                ref = x
            elif ref - x >= amp:
                direction, ref, reversals = -1, x, reversals + 1
        else:
            if x < ref:
                ref = x
            elif x - ref >= amp:
                direction, ref, reversals = 1, x, reversals + 1
    return reversals


class MotionTracker:
    def __init__(self, window_s: float = 1.2, speed_window_s: float = 0.30,
                 still_speed: float = 0.20, rearm_still_s: float = 0.25,
                 swipe_window_s: float = 0.70, swipe_min_dist: float = 0.28,
                 swipe_straightness: float = 0.75, swipe_axis_ratio: float = 2.0,
                 swipe_min_peak_speed: float = 0.60, wave_min_amp: float = 0.035,
                 wave_min_reversals: int = 3, open_fraction: float = 0.60,
                 cooldown_s: float = 1.2, lost_s: float = 0.30):
        self.window_s, self.speed_window_s = window_s, speed_window_s
        self.still_speed, self.rearm_still_s = still_speed, rearm_still_s
        self.swipe_window_s, self.swipe_min_dist = swipe_window_s, swipe_min_dist
        self.swipe_straightness, self.swipe_axis_ratio = swipe_straightness, swipe_axis_ratio
        self.swipe_min_peak_speed = swipe_min_peak_speed
        self.wave_min_amp, self.wave_min_reversals = wave_min_amp, wave_min_reversals
        self.open_fraction, self.cooldown_s, self.lost_s = open_fraction, cooldown_s, lost_s
        self.reset()

    def reset(self) -> None:
        self.samples: Deque[Tuple[float, float, float, bool]] = deque()
        self.armed = False
        self.still_since: Optional[float] = None
        self.cooldown_until = 0.0
        self.last_seen: Optional[float] = None
        self.state = MotionState()

    # ------------------------------------------------------------------ update
    def update(self, t: float, center: Optional[Tuple[float, float]], aspect: float = 1.0,
               open_palm: bool = False) -> MotionState:
        """Feed one frame. `center` is the normalised palm centre or None if no hand."""
        if center is None:
            if self.last_seen is not None and t - self.last_seen > self.lost_s:
                self.reset()
            self.state = MotionState()
            return self.state
        self.last_seen = t
        if t < self.cooldown_until:
            self.samples.clear()
            self.armed, self.still_since = False, None
            self.state = MotionState()
            return self.state

        self.samples.append((t, center[0] * aspect, center[1], bool(open_palm)))
        while self.samples and t - self.samples[0][0] > self.window_s:
            self.samples.popleft()
        self.state = self._motion_state(t)

        if self.state.speed < self.still_speed and len(self.samples) >= 2:
            if self.still_since is None:
                self.still_since = t
            elif t - self.still_since >= self.rearm_still_s:
                self.armed = True
        else:
            self.still_since = None
        return self.state

    def _recent(self, t: float, span: float) -> List[Tuple[float, float, float, bool]]:
        return [s for s in self.samples if t - s[0] <= span]

    def _motion_state(self, t: float) -> MotionState:
        pts = self._recent(t, self.speed_window_s)
        if len(pts) < 2:
            return MotionState()
        dt = pts[-1][0] - pts[0][0]
        if dt <= 0:
            return MotionState()
        dx, dy = pts[-1][1] - pts[0][1], pts[-1][2] - pts[0][2]
        path = sum(math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(pts, pts[1:]))
        speed = path / dt
        moving = speed >= self.still_speed
        if moving:
            direction = ("Right" if dx > 0 else "Left") if abs(dx) >= abs(dy) else ("Down" if dy > 0 else "Up")
        else:
            direction = "Still"
        return MotionState(speed, dx, dy, path, direction, moving)

    # ------------------------------------------------------------------ detect
    def detect(self, t: float) -> Optional[DynamicEvent]:
        """Return a dynamic gesture event if the recent trajectory matches one."""
        if not self.armed or t < self.cooldown_until or len(self.samples) < 4:
            return None
        event = self._detect_wave(t) or self._detect_swipe(t)
        if event:
            self.cooldown_until = t + self.cooldown_s
            self.samples.clear()
            self.armed, self.still_since = False, None
        return event

    def _open_ok(self, pts) -> bool:
        return sum(1 for s in pts if s[3]) / len(pts) >= self.open_fraction

    def _detect_wave(self, t: float) -> Optional[DynamicEvent]:
        pts = list(self.samples)
        if not self._open_ok(pts):
            return None
        xs, ys = [p[1] for p in pts], [p[2] for p in pts]
        rev = count_reversals(xs, self.wave_min_amp)
        x_range, y_range = max(xs) - min(xs), max(ys) - min(ys)
        if rev >= self.wave_min_reversals and y_range <= x_range:
            conf = min(1.0, 0.6 + 0.1 * (rev - self.wave_min_reversals + 1))
            return DynamicEvent("WAVE", conf, f"{rev} direction changes, side-to-side range {x_range:.2f}", t)
        return None

    def _detect_swipe(self, t: float) -> Optional[DynamicEvent]:
        pts = self._recent(t, self.swipe_window_s)
        if len(pts) < 3 or not self._open_ok(pts):
            return None
        dx, dy = pts[-1][1] - pts[0][1], pts[-1][2] - pts[0][2]
        net = math.hypot(dx, dy)
        path = sum(math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(pts, pts[1:]))
        if net < self.swipe_min_dist or path <= 0 or net / path < self.swipe_straightness:
            return None
        major, minor = max(abs(dx), abs(dy)), min(abs(dx), abs(dy))
        if minor > 0 and major / minor < self.swipe_axis_ratio:
            return None
        peak = 0.0
        for a, b in zip(pts, pts[1:]):
            dt = b[0] - a[0]
            if dt > 0:
                peak = max(peak, math.hypot(b[1] - a[1], b[2] - a[2]) / dt)
        if peak < self.swipe_min_peak_speed:
            return None
        if abs(dx) >= abs(dy):
            key = "SWIPE_RIGHT" if dx > 0 else "SWIPE_LEFT"
        else:
            key = "SWIPE_DOWN" if dy > 0 else "SWIPE_UP"
        conf = min(1.0, 0.5 * (net / path) + 0.5 * min(1.0, net / (2 * self.swipe_min_dist)))
        return DynamicEvent(key, conf, f"moved {net:.2f} frame-heights, peak speed {peak:.1f}/s", t)
