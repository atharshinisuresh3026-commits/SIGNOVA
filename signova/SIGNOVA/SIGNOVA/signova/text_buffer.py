"""Sentence buffer that turns recognised words into text."""
from __future__ import annotations

from typing import List

from .config import MAX_WORDS


class TextBuffer:
    def __init__(self) -> None:
        self.words: List[str] = []

    def add(self, word: str) -> bool:
        word = (word or "").strip()
        if not word or len(self.words) >= MAX_WORDS:
            return False
        self.words.append(word)
        return True

    def delete_last(self) -> bool:
        if not self.words:
            return False
        self.words.pop()
        return True

    def clear(self) -> None:
        self.words.clear()

    def set_text(self, text: str) -> None:
        """Replace the buffer with manually edited text."""
        self.words = (text or "").split()[:MAX_WORDS]

    @property
    def text(self) -> str:
        return " ".join(self.words)

    def __len__(self) -> int:
        return len(self.words)
