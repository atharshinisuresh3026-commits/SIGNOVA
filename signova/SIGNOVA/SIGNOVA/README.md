# SIGNOVA - Real-Time Sign Language to Text Converter

SIGNOVA turns hand gestures shown to a webcam into text. It is a complete Python application:
**webcam -> hand tracking -> gesture recognition -> text -> speech / history**, with a dark, purple-accented
interface built entirely in Streamlit.

> **Scope, stated plainly.** SIGNOVA recognises a small, *app-defined* vocabulary of
> **7 hand poses and 5 hand motions** and maps each to a word chosen by this project. It is **not** a
> complete sign-language translator. ASL, ISL, BSL and other sign languages use two hands, facial
> expression, body movement and their own grammar, none of which are modelled here. The gesture words
> are labels, not official signs.

## Supported gesture vocabulary

| Type | Gesture | How to make it | Word added |
|---|---|---|---|
| Pose | Open Palm | four fingers straight, palm to camera | Hello |
| Pose | Closed Fist | all fingers curled, thumb tucked | Stop |
| Pose | Thumbs Up | fingers curled, thumb straight up | Yes |
| Pose | One Finger | index finger only | One |
| Pose | Two Fingers | index + middle | Two |
| Pose | Three Fingers | index + middle + ring | Three |
| Pose | Love Sign | thumb + index + pinky | Love |
| Motion | Wave | open palm, wave side to side 3+ times | Goodbye |
| Motion | Swipe Right / Left | open palm, one quick sweep | Go / No |
| Motion | Swipe Up / Down | open palm, one quick sweep | Please / Thank you |

Anything else is shown as **Unknown gesture** and never adds text. Edit the words in
`signova/gestures.py`.

## Features

- **Home page** with introduction, navigation, feature overview and a *Start Converting* button.
- **Live camera** with Start/Stop, camera and hand-detection status, and clear error messages
  (camera busy, permission denied, no camera, MediaPipe missing).
- **Hand tracking**: OpenCV + MediaPipe, 21 landmarks per hand, skeleton drawn on the video,
  finger states, hand orientation and palm movement (direction, speed, distance).
- **Pose recognition** from landmark geometry in plain Python/NumPy, with a match-quality score
  and an *Unknown gesture* fallback when the pose is uncertain.
- **Motion recognition** from palm-centre trajectories over about one second of frames.
- **Text conversion**: hold a pose about 0.8 s to add its word. One hold adds one word; the same
  word is only added again after you release or change the pose. Buttons: delete last word, clear,
  edit the text directly, save.
- **Text-to-speech**: system voice (pyttsx3) with speed/volume/stop, plus a browser-voice fallback;
  empty text and missing engines are handled with messages.
- **History** in SQLite with timestamps: view, search, open, delete one, delete all, export CSV.
- **Privacy**: frames are processed locally, nothing is stored or uploaded, the camera is released
  on Stop or when you leave the Converter page.

## Windows installation and run

Requirements: Windows 10/11, a webcam, and **Python 3.9 - 3.12** (3.11 recommended; MediaPipe does
not yet support newer versions). Get Python from <https://www.python.org/downloads/windows/> and tick
*Add python.exe to PATH*.

Open PowerShell in the SIGNOVA folder and run:

```powershell
# one-time setup: creates .venv, installs packages, runs the self-tests
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1

# start the app (opens http://localhost:8501)
powershell -ExecutionPolicy Bypass -File .\run_signova.ps1
```

Or double-click `setup_windows.bat` once, then `run_signova.bat`.

Manual alternative:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

### Troubleshooting

| Problem | Fix |
|---|---|
| "Could not open camera" | Close Zoom/Teams/Windows Camera. Windows Settings > Privacy & security > Camera > allow desktop apps. Try another camera number in the sidebar. |
| MediaPipe error about `solutions` | Newer MediaPipe releases dropped the classic Hands API. Run `pip install "mediapipe>=0.10.14,<0.10.22"`. |
| `pip install mediapipe` fails | Use Python 3.9-3.12 (64-bit). Check with `python --version`. |
| Poses often show Unknown | More light, plain background, hand 30-60 cm away, lower *Recognition strictness*. |
| No system voice | `pip install pyttsx3`, or use *Speak in browser*. |
| Check everything | `python tools\check_environment.py` |

SIGNOVA opens the webcam from the Python process, so run it on your own PC (`localhost`), not on a
remote server.

## Project structure

```
SIGNOVA/
  app.py                 entry point: page config, theme, navigation, camera release on page change
  views/                 Streamlit pages: home, converter, guide, history, about
  signova/
    camera.py            webcam capture thread, backends, error handling, release
    hand_tracker.py      MediaPipe Hands wrapper (21 landmarks, handedness)
    features.py          geometry: finger extension, angles, orientation, palm centre
    gestures.py          vocabulary + static pose classifier + match quality
    motion.py            trajectory analysis: swipes and wave
    stabilizer.py        hold-to-confirm and repeat prevention
    pipeline.py          frame -> landmarks -> gesture -> word; draws overlays
    overlay.py           OpenCV drawing (skeleton, labels, hold bar)
    text_buffer.py       sentence building, delete, clear, edit
    database.py          SQLite history
    tts.py, tts_worker.py  text-to-speech in a separate process
    state.py, ui.py      Streamlit session state, theme CSS and HTML helpers
  tests/                 unit tests with synthetic landmarks (no camera needed)
  tools/check_environment.py
  docs/                  architecture, testing, report outline, viva Q&A
  .streamlit/config.toml dark theme, usage statistics off
```

## Architecture

```
                 +------------------------------ Streamlit UI (Python) ------------------------------+
                 |  Home | Converter | Gesture guide | History | About        sidebar settings        |
                 +--------------------------------------+--------------------------------------------+
                                                        | st.fragment tick (~14 Hz)
 Webcam --> Camera thread --> latest frame --> SignovaPipeline
 (OpenCV)   (camera.py)        |                 |
                               |                 +--> HandTracker (MediaPipe) --> 21 landmarks / hand
                               |                 +--> features + gestures.py  --> pose + match quality
                               |                 +--> motion.py               --> wave / swipe event
                               |                 +--> stabilizer.py           --> one word per hold
                               |                 +--> overlay.py              --> annotated frame
                               v                                   |
                     annotated video panel <-----------------------+
                                                                   v
                                    TextBuffer --> editable sentence --> tts.py (speech)
                                                         |
                                                         v
                                                 database.py (SQLite history)
```

A Mermaid version is in `docs/ARCHITECTURE.md`.

## How recognition works

1. MediaPipe returns 21 (x, y, z) landmarks. Coordinates are rescaled by the frame aspect ratio.
2. Each finger gets an **extension score** (0 curled .. 1 straight) from joint angles and fingertip
   reach; the thumb uses its joint angle and its distance from the pinky knuckle.
3. Rules map finger states to a pose. **Match quality** is how decisively the fingers sit on one side of
   the threshold. It is a heuristic, **not a probability and not an accuracy figure**.
4. The palm centre is tracked over about 1.2 s. A swipe needs a long, straight, fast, mostly
   horizontal or vertical path; a wave needs 3+ direction reversals. Motions use an open palm and a
   brief steady start, and a 1.2 s cooldown stops the return movement from firing a second event.
5. A pose is added only after a steady hold (default 0.8 s) and then latched until released.

## Calibration and honesty about accuracy

The thresholds in `features.py` and `gestures.py` are reasoned starting values. They are covered by
automated tests on synthetic hands, **but have not been validated in a user study**, and results vary
with camera, lighting, hand size and distance. Use *Show debug values* in the sidebar to see live
extension scores and adjust thresholds if a pose is mis-read. No accuracy percentage is claimed.

## Testing

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

See `docs/TESTING.md` for the unit-test list and the manual camera/UI checklist.

## Documentation

- `docs/ARCHITECTURE.md` - diagram and module responsibilities
- `docs/TESTING.md` - automated and manual testing
- `docs/REPORT_OUTLINE.md` - project report outline
- `docs/VIVA.md` - viva questions with answers

## Limitations and future work

Small fixed vocabulary; one primary hand drives text; no fingerspelling, two-handed signs, facial
cues or grammar; thresholds need per-user calibration; display rate depends on the PC (about 10-15 fps
typical). Future work: a trained landmark classifier on a collected dataset, per-user calibration
screen, two-hand and sequence models, and a proper validation study.
