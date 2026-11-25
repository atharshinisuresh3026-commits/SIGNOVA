"""Webcam access with a background reader thread (always serves the newest frame)."""
from __future__ import annotations

import sys
import threading
import time
from typing import Optional, Tuple

import cv2
import numpy as np


class CameraError(RuntimeError):
    """Raised with a user-readable message when the camera cannot be used."""


def _backends() -> list:
    if sys.platform.startswith("win"):
        return [getattr(cv2, "CAP_DSHOW", 0), getattr(cv2, "CAP_MSMF", 0), 0]
    return [0]


class Camera:
    def __init__(self, index: int = 0, width: int = 640, height: int = 480):
        self.index, self.width, self.height = index, width, height
        self._cap: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._frame: Optional[np.ndarray] = None
        self._frame_id = 0
        self._stop = threading.Event()
        self.error: Optional[str] = None

    # ------------------------------------------------------------------ open
    def open(self, warmup_s: float = 4.0) -> None:
        tried = []
        for backend in _backends():
            cap = cv2.VideoCapture(self.index, backend) if backend else cv2.VideoCapture(self.index)
            if not cap.isOpened():
                cap.release()
                tried.append(backend)
                continue
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            deadline = time.monotonic() + warmup_s
            ok = False
            while time.monotonic() < deadline:
                ok, frame = cap.read()
                if ok and frame is not None and frame.size:
                    break
                time.sleep(0.05)
            if ok:
                self._cap = cap
                with self._lock:
                    self._frame, self._frame_id = frame, 1
                self._stop.clear()
                self._thread = threading.Thread(target=self._reader, name="signova-camera", daemon=True)
                self._thread.start()
                return
            cap.release()
        raise CameraError(
            f"Could not open camera {self.index}. Close other apps that use the webcam "
            "(Zoom, Teams, Windows Camera), check Windows Settings > Privacy & security > Camera "
            "(allow desktop apps), or pick a different camera number in the sidebar."
        )

    # ------------------------------------------------------------------ loop
    def _reader(self) -> None:
        failures = 0
        while not self._stop.is_set() and self._cap is not None:
            ok, frame = self._cap.read()
            if ok and frame is not None:
                failures = 0
                with self._lock:
                    self._frame = frame
                    self._frame_id += 1
            else:
                failures += 1
                if failures > 150:
                    self.error = "The camera stopped sending frames (was it unplugged or taken by another app?)."
                    break
                time.sleep(0.01)

    def read(self) -> Tuple[Optional[np.ndarray], int]:
        with self._lock:
            return self._frame, self._frame_id

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._thread is not None and self._thread.is_alive()

    # --------------------------------------------------------------- release
    def release(self) -> None:
        """Stop the reader thread and free the camera device."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._cap is not None:
            try:
                self._cap.release()
            finally:
                self._cap = None
        with self._lock:
            self._frame = None

    def __del__(self) -> None:  # best effort if the session is garbage collected
        try:
            self.release()
        except Exception:
            pass
