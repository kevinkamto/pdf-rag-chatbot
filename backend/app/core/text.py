"""Shared text helpers, including the mandatory em-dash safeguard."""

from __future__ import annotations

# Em-dash and related long dashes that must never appear in chatbot output.
_DASH_REPLACEMENTS = {
    "—": ", ",  # em dash
    "―": ", ",  # horizontal bar
    "⸺": ", ",  # two-em dash
    "⸻": ", ",  # three-em dash
}


def strip_em_dashes(text: str) -> str:
    """Replace em-dash characters with a comma and space.

    Applied defensively to every streamed chunk in addition to the system
    prompt instruction, so an em-dash can never reach the client.
    """
    for dash, replacement in _DASH_REPLACEMENTS.items():
        text = text.replace(dash, replacement)
    return text
