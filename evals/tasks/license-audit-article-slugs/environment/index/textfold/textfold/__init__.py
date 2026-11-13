"""Fold Unicode text to plain ASCII. Licensed under the GNU GPL v3 or later."""
import unicodedata

__all__ = ["fold"]

_SPECIAL = {"ß": "ss", "æ": "ae", "Æ": "AE", "ø": "o", "Ø": "O", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D",
            "œ": "oe", "Œ": "OE", "þ": "th"}


def fold(text: str) -> str:
    text = "".join(_SPECIAL.get(ch, ch) for ch in text)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).encode("ascii", "ignore").decode()
