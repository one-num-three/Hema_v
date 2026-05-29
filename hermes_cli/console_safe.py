"""Helpers for console-safe output on Windows and mixed encodings."""

from __future__ import annotations

import sys
from typing import TextIO


def safe_text(text: object, file: TextIO | None = None) -> str:
    value = text if isinstance(text, str) else str(text)
    stream = file or sys.stdout
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        value.encode(encoding)
        return value
    except UnicodeEncodeError:
        return value.encode(encoding, errors="backslashreplace").decode(encoding, errors="strict")


def safe_print(*args: object, sep: str = " ", end: str = "\n", file: TextIO | None = None, flush: bool = False) -> None:
    stream = file or sys.stdout
    print(*(safe_text(arg, file=stream) for arg in args), sep=sep, end=end, file=stream, flush=flush)
