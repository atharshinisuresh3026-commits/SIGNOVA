"""Quick diagnostics: python tools/check_environment.py  (run inside the virtual environment)."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def check(name):
    try:
        mod = importlib.import_module(name)
        print(f"[ok]   {name} {getattr(mod, '__version__', '')}")
        return mod
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")


print("Python", sys.version.split()[0])
for lib in ("streamlit", "cv2", "numpy", "pyttsx3", "sqlite3"):
    check(lib)
mp = check("mediapipe")
if mp is not None:
    ok = hasattr(mp, "solutions") and hasattr(mp.solutions, "hands")
    print("[ok]   mediapipe Hands solution available" if ok else
          "[FAIL] this mediapipe build has no solutions.hands - install: pip install \"mediapipe>=0.10.14,<0.10.22\"")

from signova.camera import Camera, CameraError  # noqa: E402

for index in range(3):
    cam = Camera(index)
    try:
        cam.open(warmup_s=2.0)
        frame, _ = cam.read()
        print(f"[ok]   camera {index}: {frame.shape[1]}x{frame.shape[0]}")
    except CameraError:
        print(f"[--]   camera {index}: not available")
    finally:
        cam.release()
