import unittest

import numpy as np

from signova.config import Settings
from signova.hand_tracker import HandObservation
from signova.pipeline import SignovaPipeline
from signova.text_buffer import TextBuffer
from tests.synthetic import POSES, make_hand

ASPECT = 4 / 3


def obs(lm, label="Right", score=0.95):
    return HandObservation(lm, label, score)


def run(pipe, hands_fn, seconds, t0=0.0, fps=20):
    commits, t = [], t0
    while t < t0 + seconds:
        res = pipe.process_observations(t, hands_fn(t), ASPECT)
        if res.commit:
            commits.append((res.commit.word, res.commit.source))
        t += 1.0 / fps
    return commits, t


class TestPipeline(unittest.TestCase):
    def make(self):
        return SignovaPipeline(Settings())

    def test_hold_gesture_adds_exactly_one_word(self):
        pipe = self.make()
        lm = make_hand(**POSES["THUMBS_UP"], aspect=ASPECT)
        commits, _ = run(pipe, lambda t: [obs(lm)], 5.0)
        self.assertEqual(commits, [("Yes", "static")])

    def test_sequence_builds_sentence(self):
        pipe, buf, t = self.make(), TextBuffer(), 0.0
        for key in ("OPEN_PALM", "ONE_FINGER", "FIST"):
            lm = make_hand(**POSES[key], aspect=ASPECT)
            commits, t = run(pipe, lambda _t, lm=lm: [obs(lm)], 1.5, t)
            for word, _ in commits:
                buf.add(word)
            _, t = run(pipe, lambda _t: [], 0.8, t)  # hand removed between gestures
        self.assertEqual(buf.text, "Hello One Stop")

    def test_no_hand_no_prediction(self):
        pipe = self.make()
        commits, _ = run(pipe, lambda t: [], 3.0)
        self.assertEqual(commits, [])

    def test_unknown_pose_never_adds_text(self):
        pipe = self.make()
        lm = make_hand(extended=("middle",), thumb="tucked", aspect=ASPECT)
        commits, _ = run(pipe, lambda t: [obs(lm)], 4.0)
        self.assertEqual(commits, [])

    def test_swipe_adds_dynamic_word_and_not_hello(self):
        pipe = self.make()
        palm = POSES["OPEN_PALM"]

        def hands(t):
            x = 0.0 if t < 0.6 else min(0.45, (t - 0.6) * 2.5)  # still, then sweep right
            return [obs(make_hand(**palm, dx=x - 0.1, aspect=ASPECT))]

        commits, _ = run(pipe, hands, 1.4)
        self.assertEqual(commits, [("Go", "dynamic")])
        # Holding the open palm afterwards must not add "Hello" until it is released
        lm = make_hand(**palm, dx=0.2, aspect=ASPECT)
        more, _ = run(pipe, lambda t: [obs(lm)], 3.0, 1.45)
        self.assertEqual(more, [])

    def test_two_hands_use_one_primary(self):
        pipe = self.make()
        a = make_hand(**POSES["FIST"], aspect=ASPECT)
        b = make_hand(**POSES["OPEN_PALM"], dx=0.3, aspect=ASPECT)
        commits, _ = run(pipe, lambda t: [obs(a, "Right", 0.99), obs(b, "Left", 0.9)], 3.0)
        self.assertEqual(commits, [("Stop", "static")])


if __name__ == "__main__":
    unittest.main()
