"""Hold-to-confirm logic that stops a held gesture from being added repeatedly."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

UNKNOWN = "UNKNOWN"


@dataclass
class StabilizerOutput:
    candidate: Optional[str]
    progress: float            # 0..1 hold progress for the candidate
    committed: Optional[str]   # gesture key committed on THIS frame (once per hold)
    latched: bool              # True while waiting for the gesture to be released


class HoldConfirmer:
    """A gesture is committed once it has been held steadily for `hold_s`.

    After a commit the confirmer is *latched*: the same gesture cannot be added
    again until the hand shows a different gesture (or disappears) for `release_s`.
    Short glitches (<= `grace_s`) do not reset the hold timer.
    """

    def __init__(self, hold_s: float = 0.8, grace_s: float = 0.25,
                 release_s: float = 0.40, max_speed: float = 0.25):
        self.hold_s, self.grace_s = hold_s, grace_s
        self.release_s, self.max_speed = release_s, max_speed
        self.reset()

    def reset(self) -> None:
        self.candidate: Optional[str] = None
        self.cand_start = 0.0
        self.mismatch_start: Optional[float] = None
        self.latched_key: Optional[str] = None
        self.unlatch_start: Optional[float] = None

    def latch(self, key: Optional[str]) -> None:
        """Force-latch (used after a motion gesture so the held pose is not re-added)."""
        self.candidate, self.mismatch_start = None, None
        self.latched_key = key
        self.unlatch_start = None

    def update(self, t: float, key: Optional[str], speed: float = 0.0) -> StabilizerOutput:
        valid = key is not None and key != UNKNOWN and speed <= self.max_speed

        if self.latched_key is not None:
            if key == self.latched_key:
                self.unlatch_start = None
            elif self.unlatch_start is None:
                self.unlatch_start = t
            elif t - self.unlatch_start >= self.release_s:
                self.latched_key, self.unlatch_start = None, None
                self.candidate, self.mismatch_start = None, None
            if self.latched_key is not None:
                return StabilizerOutput(self.latched_key, 1.0, None, True)

        if not valid:
            if self.candidate is not None:
                if self.mismatch_start is None:
                    self.mismatch_start = t
                elif t - self.mismatch_start > self.grace_s:
                    self.candidate, self.mismatch_start = None, None
            return StabilizerOutput(self.candidate, self._progress(t), None, False)

        if self.candidate is None:
            self.candidate, self.cand_start, self.mismatch_start = key, t, None
        elif key != self.candidate:
            if self.mismatch_start is None:
                self.mismatch_start = t
            elif t - self.mismatch_start > self.grace_s:
                self.candidate, self.cand_start, self.mismatch_start = key, t, None
        else:
            self.mismatch_start = None

        if key == self.candidate and t - self.cand_start >= self.hold_s:
            committed = self.candidate
            self.latched_key, self.unlatch_start = committed, None
            return StabilizerOutput(committed, 1.0, committed, True)
        return StabilizerOutput(self.candidate, self._progress(t), None, False)

    def _progress(self, t: float) -> float:
        if self.candidate is None or self.hold_s <= 0:
            return 0.0
        return max(0.0, min(1.0, (t - self.cand_start) / self.hold_s))
