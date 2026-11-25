import unittest

from signova.stabilizer import HoldConfirmer


def run(c, key, start, end, step=0.05, speed=0.0):
    out, t, commits = None, start, []
    while t <= end + 1e-9:
        out = c.update(t, key, speed)
        if out.committed:
            commits.append((round(t, 2), out.committed))
        t += step
    return commits, out


class TestHoldConfirmer(unittest.TestCase):
    def test_commit_once_while_held(self):
        c = HoldConfirmer(hold_s=0.8)
        commits, out = run(c, "OPEN_PALM", 0.0, 5.0)
        self.assertEqual(len(commits), 1)
        self.assertTrue(out.latched)
        self.assertGreaterEqual(commits[0][0], 0.8)

    def test_no_commit_if_held_too_briefly(self):
        c = HoldConfirmer(hold_s=0.8)
        commits, _ = run(c, "FIST", 0.0, 0.5)
        self.assertEqual(commits, [])

    def test_repeat_after_release(self):
        c = HoldConfirmer(hold_s=0.8)
        c1, _ = run(c, "FIST", 0.0, 1.2)
        _, _ = run(c, None, 1.25, 2.0)        # hand removed
        c2, _ = run(c, "FIST", 2.05, 3.2)
        self.assertEqual(len(c1) + len(c2), 2)

    def test_changing_gesture_commits_new_word(self):
        c = HoldConfirmer(hold_s=0.8)
        c1, _ = run(c, "FIST", 0.0, 1.2)
        c2, _ = run(c, "OPEN_PALM", 1.25, 3.0)
        self.assertEqual([k for _, k in c1 + c2], ["FIST", "OPEN_PALM"])

    def test_short_flicker_does_not_repeat_or_reset(self):
        c = HoldConfirmer(hold_s=0.8)
        commits, _ = run(c, "FIST", 0.0, 1.0)
        more, _ = run(c, "UNKNOWN", 1.05, 1.25)   # 0.2 s glitch
        more2, _ = run(c, "FIST", 1.3, 4.0)
        self.assertEqual(len(commits) + len(more) + len(more2), 1)

    def test_flicker_before_commit_is_tolerated(self):
        c = HoldConfirmer(hold_s=0.8, grace_s=0.25)
        run(c, "FIST", 0.0, 0.5)
        run(c, "UNKNOWN", 0.55, 0.65)
        commits, _ = run(c, "FIST", 0.7, 1.5)
        self.assertEqual(len(commits), 1)

    def test_fast_motion_blocks_commit(self):
        c = HoldConfirmer(hold_s=0.8)
        commits, _ = run(c, "OPEN_PALM", 0.0, 3.0, speed=1.0)
        self.assertEqual(commits, [])

    def test_unknown_never_commits(self):
        c = HoldConfirmer(hold_s=0.8)
        commits, _ = run(c, "UNKNOWN", 0.0, 3.0)
        self.assertEqual(commits, [])

    def test_force_latch(self):
        c = HoldConfirmer(hold_s=0.8)
        c.latch("OPEN_PALM")
        commits, _ = run(c, "OPEN_PALM", 0.0, 3.0)
        self.assertEqual(commits, [])


if __name__ == "__main__":
    unittest.main()
