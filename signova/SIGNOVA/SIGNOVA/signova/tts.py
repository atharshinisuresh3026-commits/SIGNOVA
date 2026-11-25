"""Text-to-speech controller: system voice via pyttsx3 (subprocess) + browser fallback."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from typing import List, Optional, Tuple

from .config import PROJECT_ROOT


class TextToSpeech:
    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None

    @staticmethod
    def engine_installed() -> bool:
        return importlib.util.find_spec("pyttsx3") is not None

    def _popen(self, args: List[str]) -> subprocess.Popen:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return subprocess.Popen(
            [sys.executable, "-m", "signova.tts_worker", *args],
            cwd=str(PROJECT_ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, creationflags=flags,
        )

    def speak(self, text: str, rate: int = 170, volume: float = 1.0, voice: str = "") -> Tuple[bool, str]:
        """Start speaking. Returns (ok, message). Never raises."""
        text = (text or "").strip()
        if not text:
            return False, "There is no text to read yet. Add words with gestures or type in the text box."
        if not self.engine_installed():
            return False, ("The system speech engine (pyttsx3) is not installed. Run "
                           "'pip install pyttsx3' or use the browser voice button instead.")
        self.stop()
        try:
            proc = self._popen([])
            proc.stdin.write(json.dumps({"text": text, "rate": rate, "volume": volume, "voice": voice}))
            proc.stdin.close()
        except Exception as exc:
            return False, f"Could not start the speech engine: {exc}"
        self._proc = proc
        time.sleep(0.8)  # catch immediate failures (no voice engine, bad install)
        code = proc.poll()
        if code not in (None, 0):
            err = (proc.stderr.read() or "").strip() if proc.stderr else ""
            self._proc = None
            return False, err or f"Speech engine exited with code {code}."
        return True, "Speaking..."

    def is_speaking(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def stop(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except Exception:
                self._proc.kill()
        self._proc = None

    def list_voices(self) -> List[dict]:
        if not self.engine_installed():
            return []
        try:
            proc = self._popen(["--voices"])
            out, _ = proc.communicate(timeout=10)
            return json.loads(out or "[]")
        except Exception:
            return []
