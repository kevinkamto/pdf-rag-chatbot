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


def test_is_idempotent() -> None:
    once = strip_em_dashes("a — b ― c")
    assert strip_em_dashes(once) == once


def test_each_dash_maps_to_comma_space() -> None:
    for dash in ("—", "―", "⸺", "⸻"):
        assert strip_em_dashes(f"a{dash}b") == "a, b"


def test_streamed_chunk_with_only_a_dash() -> None:
    # Replies stream chunk by chunk; a chunk may be a lone dash.
    assert strip_em_dashes("—") == ", "
