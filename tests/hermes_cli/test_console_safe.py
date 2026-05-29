from __future__ import annotations

from io import StringIO

from hermes_cli.console_safe import safe_print, safe_text


class _Cp936Buffer(StringIO):
    encoding = "cp936"


def test_safe_text_escapes_unencodable_characters():
    text = "bad surrogate \udcff and check ✓"
    rendered = safe_text(text, file=_Cp936Buffer())
    assert "\\udcff" in rendered
    assert "✓" not in rendered


def test_safe_print_writes_console_safe_text():
    buffer = _Cp936Buffer()
    safe_print("value", "✓", file=buffer)
    assert buffer.getvalue().strip() == "value \\u2713"
