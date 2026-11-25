"""Application-wide constants and runtime settings."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

APP_NAME = "SIGNOVA"
APP_TAGLINE = "Real-Time Sign Language to Text Converter"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "signova.db"

MAX_WORDS = 200  # safety cap for one sentence


@dataclass
class Settings:
    """User-adjustable settings (set from the converter sidebar)."""

    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    mirror: bool = True
    max_hands: int = 1
    hold_seconds: float = 0.8       # how long a pose must be held to be added
    min_quality: float = 0.40       # below this a pose is reported as "Unknown"
    show_indices: bool = False      # draw landmark numbers 0..20
    min_detection_confidence: float = 0.6
    min_tracking_confidence: float = 0.5
    model_complexity: int = 1
