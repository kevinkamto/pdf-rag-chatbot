from __future__ import annotations

import pytest
from app.core.config import Settings
from pydantic import ValidationError


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {"openai_api_key": "test-key"}
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_overlap_equal_to_chunk_size_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _settings(chunk_tokens=200, chunk_overlap_tokens=200)


def test_overlap_above_chunk_size_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _settings(chunk_tokens=200, chunk_overlap_tokens=400)


def test_overlap_below_chunk_size_is_accepted() -> None:
    settings = _settings(chunk_tokens=200, chunk_overlap_tokens=50)
    assert settings.chunk_overlap_tokens < settings.chunk_tokens


def test_non_positive_chunk_size_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _settings(chunk_tokens=0)
