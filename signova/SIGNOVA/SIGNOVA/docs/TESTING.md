# Testing SIGNOVA

## 1. Automated tests (no camera needed)

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

They use synthetic landmark hands (`tests/synthetic.py`), so they verify the **rules and logic**, not
real-world accuracy.

| File | What it checks |
|---|---|
| `test_gestures.py` | All 7 poses recognised at 4:3 and 16:9; unsupported and ambiguous poses give Unknown; position shifts do not matter; quality gate; orientation |
| `test_motion.py` | 4 swipe directions, wave, slow drift / jitter / diagonal / fast entry ignored, open palm required, cooldown, hand-loss reset |
| `test_stabilizer.py` | One word per hold, no word for short holds, repeat only after release, flicker tolerance, fast motion blocks commits |
| `test_pipeline.py` | End-to-end landmarks -> words, sentence building, no hand = no text, unknown never adds text, swipe does not also add "Hello", two hands |
| `test_text_and_db.py` | Add/delete/clear/edit, SQLite save/list/search/delete/clear, empty input rejected, injection-safe |

## 2. Manual camera and UI checklist

| # | Step | Expected |
|---|---|---|
| 1 | Open Home | Dark purple page, *Start Converting* works |
| 2 | Converter > Start camera | Spinner, then live video, badge "Camera live" |
| 3 | Raise a hand | Skeleton with 21 points, "1 hand detected" |
| 4 | Lower hand | "No hand detected", no text added |
| 5 | Hold Open Palm ~1 s | Progress bar fills, "Hello" added once; keep holding: nothing more |
| 6 | Lower hand, show Open Palm again | "Hello" added again |
| 7 | Try Fist, Thumbs Up, One/Two/Three fingers, Love | Matching words |
| 8 | Show an unsupported pose | "Unknown gesture", nothing added |
| 9 | Wave / swipe | Motion recognised once; no extra "Hello" |
| 10 | Delete last word, Clear, edit text box | Text updates correctly |
| 11 | Save to history, open History | Entry with timestamp; delete works |
| 12 | Speak with empty text | Warning, no crash |
| 13 | Speak with text / Speak in browser | Audio plays; Stop works |
| 14 | Stop camera | Video stops; webcam light turns off |
| 15 | Start, then open another page | Camera is released automatically |
| 16 | Start with another app using the webcam | Clear error message |
| 17 | Narrow the browser window | Layout stacks, nothing overflows |

## 3. Calibrating on your own hand

Tick *Show debug values*. Each finger shows an extension score; values above 0.5 count as extended.
If a pose is misread, adjust the thresholds in `features.py` (`finger_extension`, `thumb_extension`) or
`gestures.py` (`thumb_up_min`), then rerun the tests.

## 4. Reporting results honestly

Report per-gesture counts from your own trials (for example 20 attempts per gesture, per person,
lighting condition) instead of a single percentage, and state the camera and conditions.
