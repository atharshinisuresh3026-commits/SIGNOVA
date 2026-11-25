# SIGNOVA architecture

```mermaid
flowchart LR
    CAM[Webcam] --> CT[Camera thread<br/>camera.py]
    CT --> PL[SignovaPipeline<br/>pipeline.py]
    PL --> HT[HandTracker<br/>MediaPipe, 21 landmarks]
    HT --> F[features.py<br/>finger extension, orientation]
    F --> G[gestures.py<br/>pose + match quality]
    HT --> M[motion.py<br/>wave / swipe]
    G --> S[stabilizer.py<br/>hold-to-confirm, no repeats]
    M --> S
    S --> TB[TextBuffer<br/>sentence]
    PL --> OV[overlay.py<br/>skeleton + HUD]
    OV --> UI[Streamlit Converter page<br/>video | recognition panel]
    TB --> UI
    UI --> TTS[tts.py<br/>pyttsx3 / browser voice]
    UI --> DB[(SQLite history)]
```

## Responsibilities

| Module | Responsibility |
|---|---|
| `camera.py` | Opens the webcam (DirectShow/MSMF on Windows), reads frames in a thread, reports errors, releases the device |
| `hand_tracker.py` | Runs MediaPipe Hands locally; returns landmarks and handedness |
| `features.py` | Pure geometry on landmark arrays (testable without a camera) |
| `gestures.py` | Vocabulary, rule-based classifier, match-quality score, Unknown fallback |
| `motion.py` | Palm trajectory analysis for wave and four swipe directions |
| `stabilizer.py` | Hold timer, latch and grace period so one hold gives one word |
| `pipeline.py` | Orchestrates one frame; draws the overlay; returns a `FrameResult` |
| `text_buffer.py`, `database.py` | Sentence state and SQLite persistence |
| `tts.py` | Speech in a separate process, so the UI never freezes |
| `state.py`, `ui.py`, `views/` | Streamlit session handling, theme and pages |

## Data flow and design decisions

- **Why a camera thread?** It always holds the newest frame, so processing never lags behind.
- **Why `st.fragment(run_every=...)`?** The live panel refreshes on a timer while buttons and the text box
  stay interactive; only a committed word triggers a full page refresh.
- **Why classification is separate from Streamlit.** `pipeline.process_observations` takes landmarks
  and returns results, so all recognition logic is unit-tested without a camera.
- **Privacy.** Frames live only in memory; the database stores text only.
