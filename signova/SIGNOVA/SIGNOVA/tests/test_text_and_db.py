import os
import tempfile
import unittest

from signova.database import HistoryDB
from signova.text_buffer import TextBuffer


class TestTextBuffer(unittest.TestCase):
    def test_add_delete_clear(self):
        b = TextBuffer()
        self.assertTrue(b.add("Hello"))
        self.assertTrue(b.add("Yes"))
        self.assertEqual(b.text, "Hello Yes")
        self.assertTrue(b.delete_last())
        self.assertEqual(b.text, "Hello")
        b.clear()
        self.assertEqual(b.text, "")
        self.assertFalse(b.delete_last())

    def test_blank_word_rejected(self):
        self.assertFalse(TextBuffer().add("   "))

    def test_manual_edit(self):
        b = TextBuffer()
        b.set_text("  hello   world  ")
        self.assertEqual(b.words, ["hello", "world"])


class TestHistoryDB(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = HistoryDB(os.path.join(self.dir.name, "t.db"))

    def tearDown(self):
        self.dir.cleanup()

    def test_add_list_delete(self):
        a = self.db.add("Hello Yes")
        b = self.db.add("Go Stop")
        rows = self.db.list()
        self.assertEqual([r.id for r in rows], [b, a])  # newest first
        self.assertEqual(rows[0].word_count, 2)
        self.assertRegex(rows[0].created_at, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertTrue(self.db.delete(a))
        self.assertFalse(self.db.delete(a))
        self.assertEqual(self.db.count(), 1)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            self.db.add("   ")

    def test_search_and_clear(self):
        self.db.add("Hello Yes")
        self.db.add("Go Stop")
        self.assertEqual(len(self.db.list(search="stop")), 1)
        self.assertEqual(self.db.clear(), 2)
        self.assertEqual(self.db.count(), 0)

    def test_sql_injection_is_inert(self):
        self.db.add("x'); DROP TABLE translations;--")
        self.assertEqual(self.db.count(), 1)


if __name__ == "__main__":
    unittest.main()
