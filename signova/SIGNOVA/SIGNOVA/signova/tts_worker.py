"""Speaks text with the system voice (pyttsx3). Runs in its own process so the
Streamlit app never blocks and a stuck speech engine can be stopped.

Usage:  python -m signova.tts_worker            (JSON on stdin: text, rate, volume, voice)
        python -m signova.tts_worker --voices   (prints installed voices as JSON)
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        import pyttsx3
    except Exception as exc:
        print(f"pyttsx3 is not installed or failed to load: {exc}", file=sys.stderr)
        return 2
    try:
        engine = pyttsx3.init()
    except Exception as exc:
        print(f"No speech engine available on this system: {exc}", file=sys.stderr)
        return 3

    if "--voices" in sys.argv:
        print(json.dumps([{"id": v.id, "name": v.name} for v in engine.getProperty("voices")]))
        return 0

    job = json.loads(sys.stdin.read() or "{}")
    text = (job.get("text") or "").strip()
    if not text:
        print("Nothing to speak.", file=sys.stderr)
        return 4
    try:
        engine.setProperty("rate", int(job.get("rate", 170)))
        engine.setProperty("volume", float(job.get("volume", 1.0)))
        if job.get("voice"):
            engine.setProperty("voice", job["voice"])
        engine.say(text)
        engine.runAndWait()
    except Exception as exc:
        print(f"Speech failed: {exc}", file=sys.stderr)
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
