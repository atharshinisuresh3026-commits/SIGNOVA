import unittest

from signova.motion import MotionTracker, count_reversals

ASPECT = 4 / 3
FPS = 20


def feed(tr, frames, t0=0.0, open_palm=True):
    """frames: list of (x, y) normalised centres. Returns (events, last_t)."""
    events, t = [], t0
    for c in frames:
        tr.update(t, c, ASPECT, open_palm)
        ev = tr.detect(t)
        if ev:
            events.append(ev.key)
        t += 1.0 / FPS
    return events, t


def still(n, x=0.5, y=0.5):
    return [(x, y)] * n


def line(n, p0, p1):
    return [(p0[0] + (p1[0] - p0[0]) * i / (n - 1), p0[1] + (p1[1] - p0[1]) * i / (n - 1)) for i in range(n)]


class TestMotion(unittest.TestCase):
    def test_swipes_in_all_four_directions(self):
        cases = {
            "SWIPE_RIGHT": ((0.2, 0.5), (0.8, 0.5)),
            "SWIPE_LEFT": ((0.8, 0.5), (0.2, 0.5)),
            "SWIPE_UP": ((0.5, 0.8), (0.5, 0.25)),
            "SWIPE_DOWN": ((0.5, 0.2), (0.5, 0.75)),
        }
        for key, (a, b) in cases.items():
            tr = MotionTracker()
            events, _ = feed(tr, still(10, *a) + line(8, a, b))
            self.assertEqual(events, [key], key)

    def test_wave_detected(self):
        import math
        tr = MotionTracker()
        wave = [(0.5 + 0.10 * math.sin(2 * math.pi * 2.5 * i / FPS), 0.5) for i in range(30)]
        events, _ = feed(tr, still(10) + wave)
        self.assertEqual(events, ["WAVE"])

    def test_wave_is_not_reported_as_swipe_and_fires_once(self):
        import math
        tr = MotionTracker()
        wave = [(0.5 + 0.10 * math.sin(2 * math.pi * 2.5 * i / FPS), 0.5) for i in range(60)]
        events, _ = feed(tr, still(10) + wave)
        self.assertEqual(events.count("WAVE"), 1)
        self.assertNotIn("SWIPE_LEFT", events[:1])

    def test_slow_drift_is_ignored(self):
        tr = MotionTracker()
        events, _ = feed(tr, still(10, 0.3) + line(40, (0.3, 0.5), (0.7, 0.5)))  # 2 s for 0.4
        self.assertEqual(events, [])

    def test_jitter_is_ignored(self):
        import random
        random.seed(1)
        tr = MotionTracker()
        frames = [(0.5 + random.uniform(-0.004, 0.004), 0.5 + random.uniform(-0.004, 0.004)) for _ in range(80)]
        events, _ = feed(tr, frames)
        self.assertEqual(events, [])

    def test_hand_entering_fast_without_settling_is_ignored(self):
        tr = MotionTracker()
        events, _ = feed(tr, line(8, (0.0, 0.5), (0.6, 0.5)))
        self.assertEqual(events, [])

    def test_requires_open_palm(self):
        tr = MotionTracker()
        events, _ = feed(tr, still(10, 0.2) + line(8, (0.2, 0.5), (0.8, 0.5)), open_palm=False)
        self.assertEqual(events, [])

    def test_diagonal_motion_is_ignored(self):
        tr = MotionTracker()
        events, _ = feed(tr, still(10, 0.2, 0.2) + line(8, (0.2, 0.2), (0.7, 0.6)))
        self.assertEqual(events, [])

    def test_cooldown_blocks_return_motion(self):
        tr = MotionTracker()
        frames = still(10, 0.2) + line(8, (0.2, 0.5), (0.8, 0.5)) + line(8, (0.8, 0.5), (0.2, 0.5))
        events, _ = feed(tr, frames)
        self.assertEqual(events, ["SWIPE_RIGHT"])

    def test_motion_state_direction_and_speed(self):
        tr = MotionTracker()
        feed(tr, still(6) + line(6, (0.5, 0.5), (0.7, 0.5)))
        st = tr.state
        self.assertEqual(st.direction, "Right")
        self.assertTrue(st.moving)
        self.assertGreater(st.speed, 0.5)

    def test_hand_loss_resets(self):
        tr = MotionTracker()
        feed(tr, still(10))
        self.assertTrue(tr.armed)
        for i in range(10):
            tr.update(1.0 + i * 0.05, None)
        self.assertFalse(tr.armed)

    def test_count_reversals(self):
        self.assertEqual(count_reversals([0, 1, 0, 1, 0], 0.5), 3)
        self.assertEqual(count_reversals([0, 0.1, 0, 0.1], 0.5), 0)


if __name__ == "__main__":
    unittest.main()
