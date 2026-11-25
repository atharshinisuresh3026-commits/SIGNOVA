import unittest

from signova.features import hand_orientation, to_metric
from signova.gestures import STATIC_GESTURES, UNKNOWN, classify_hand
from tests.synthetic import POSES, make_hand


class TestStaticGestures(unittest.TestCase):
    def test_every_supported_pose_is_recognised(self):
        for key, spec in POSES.items():
            for aspect in (1.0, 4 / 3, 16 / 9):
                res = classify_hand(make_hand(**spec, aspect=aspect), aspect)
                self.assertEqual(res.key, key, f"{key} @ aspect {aspect}: {res.reason}")
                self.assertGreater(res.quality, 0.6, key)

    def test_vocabulary_matches_required_gestures(self):
        required = {"OPEN_PALM", "FIST", "THUMBS_UP", "ONE_FINGER", "TWO_FINGERS", "THREE_FINGERS"}
        self.assertTrue(required <= set(STATIC_GESTURES))

    def test_unsupported_pose_is_unknown(self):
        # Middle finger only - not in the vocabulary
        res = classify_hand(make_hand(extended=("middle",), thumb="tucked"))
        self.assertEqual(res.key, UNKNOWN)
        self.assertEqual(res.display, "Unknown")
        self.assertEqual(res.word, "")

    def test_sideways_thumb_fist_is_unknown(self):
        res = classify_hand(make_hand(extended=(), thumb="out"))
        self.assertEqual(res.key, UNKNOWN)

    def test_ambiguous_half_curled_thumb_is_not_confident(self):
        res = classify_hand(make_hand(extended=("index",), thumb="half"))
        # must not be reported as a confident ONE_FINGER
        self.assertTrue(res.key == UNKNOWN or res.quality < 0.9)

    def test_position_shift_does_not_change_result(self):
        for key, spec in POSES.items():
            res = classify_hand(make_hand(**spec, dx=-0.2, dy=-0.1))
            self.assertEqual(res.key, key)

    def test_min_quality_gate(self):
        res = classify_hand(make_hand(**POSES["FIST"]), min_quality=0.999)
        self.assertEqual(res.key, UNKNOWN)
        self.assertIn("uncertain", res.reason)

    def test_orientation(self):
        ang, label = hand_orientation(to_metric(make_hand(**POSES["OPEN_PALM"])))
        self.assertEqual(label, "Up")
        ang2, label2 = hand_orientation(to_metric(make_hand(**POSES["OPEN_PALM"], rot90=True)))
        self.assertEqual(label2, "Right")  # rotated clockwise: fingers point to screen-right

    def test_bad_shape_raises(self):
        import numpy as np
        with self.assertRaises(ValueError):
            classify_hand(np.zeros((20, 3)))


if __name__ == "__main__":
    unittest.main()
