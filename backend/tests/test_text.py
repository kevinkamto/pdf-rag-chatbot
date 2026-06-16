from __future__ import annotations

from app.core.text import strip_em_dashes


def test_strips_em_dash() -> None:
    assert "—" not in strip_em_dashes("wait — really")
    assert strip_em_dashes("wait — really") == "wait ,  really"


def test_leaves_plain_text_untouched() -> None:
    text = "Hello, world. (parenthetical) - hyphen is fine."
    assert strip_em_dashes(text) == text


def test_strips_other_long_dashes() -> None:
    for dash in ("―", "⸺", "⸻"):
        assert dash not in strip_em_dashes(f"a{dash}b")
