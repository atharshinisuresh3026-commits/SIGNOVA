# Viva questions and answers

**1. What does SIGNOVA do?**
It reads webcam video, tracks the hand with MediaPipe, classifies a small set of poses and motions with
Python rules, and converts them into words in an editable sentence that can be spoken or saved.

**2. Is it a full sign-language translator?**
No. It recognises 7 poses and 5 motions that this project defines. Real sign languages need two hands,
facial expression, body movement and grammar. Claiming otherwise would be misleading.

**3. Why Streamlit?**
It lets the whole interface be written in Python, with built-in state, layout and reruns. The live panel
uses `st.fragment(run_every=...)` so video refreshes while other widgets stay responsive.

**4. What are the 21 landmarks?**
MediaPipe's hand model: wrist (0), thumb (1-4), index (5-8), middle (9-12), ring (13-16), pinky (17-20),
each with normalised x, y and relative depth z.

**5. How do you decide a finger is extended?**
Average of two cues: joint straightness (angles at the PIP and DIP joints) and reach (fingertip distance
from the wrist relative to the knuckle). The thumb uses its joint angle and its distance from the pinky
knuckle. A score of 0.5 or more means extended.

**6. Why scale coordinates by the aspect ratio?**
Landmarks are normalised separately in x and y, so a 16:9 frame stretches distances. Scaling x and z by
the aspect ratio restores true geometry before measuring angles and distances.

**7. What is the confidence/quality score?**
How decisively the relevant fingers are extended or curled (distance from the 0.5 threshold). It is a
heuristic match quality, not a probability, and it is not an accuracy measure.

**8. How do you handle uncertain poses?**
If no rule matches, or quality is below the strictness setting, the result is "Unknown gesture" and no text
is added.

**9. How do you stop a held gesture from repeating?**
`HoldConfirmer` needs a steady hold (0.8 s default), commits once, then latches until a different pose or
no hand appears for 0.4 s. Brief flicker (under 0.25 s) does not reset the timer or release the latch.

**10. How are dynamic gestures recognised?**
The palm centre is tracked over about 1.2 s. A swipe needs enough distance, a straight path, a dominant
axis and a minimum peak speed. A wave needs at least three direction reversals with enough amplitude and
mostly horizontal motion.

**11. Why must the hand rest before a motion?**
Arming after a short steady period avoids false swipes when a hand simply enters the frame. A 1.2 s
cooldown stops the return stroke from being read as a second gesture.

**12. Why not use a neural network?**
It needs a labelled dataset and a validation protocol. Rule-based classification on landmarks is
transparent, testable and works without training data. A trained classifier is listed as future work.

**13. How is privacy protected?**
Frames are processed in memory on the local computer, never saved or uploaded. SQLite stores only text.
The camera is released on Stop or when leaving the Converter page. Streamlit telemetry is off.

**14. What does SQLite store?**
Table `translations(id, text, word_count, created_at)`. All queries are parameterised, so input cannot
inject SQL.

**15. How does text-to-speech work?**
`pyttsx3` speaks in a separate process, so the UI never blocks and speech can be stopped. If it is missing,
a browser `speechSynthesis` button is available. Empty text gives a warning.

**16. What happens if the camera is busy or missing?**
`Camera.open` tries several Windows backends and raises a readable error, shown in the UI with fixes.

**17. How was it tested?**
Unit tests feed synthetic landmark hands and simulated trajectories through the classifier, stabilizer and
pipeline. A manual checklist covers the real camera and UI. There is no accuracy claim without a user study.

**18. What are the main limitations?**
Small vocabulary, one primary hand, lighting and camera dependence, thresholds that may need per-user
tuning, and about 10-15 displayed frames per second.

**19. How could accuracy be improved?**
Collect a labelled landmark dataset from many users, train and cross-validate a classifier, add per-user
calibration, and evaluate with Deaf and hard-of-hearing participants.

**20. Why can't it be deployed on a cloud server directly?**
OpenCV reads the camera of the machine running Python. For a hosted version you would stream browser video
to the server, which changes the privacy model, so SIGNOVA is designed to run locally.
