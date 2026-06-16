"""Shared API dependencies."""

from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_management_secret(x_management_secret: str = Header(default="")) -> None:
    """Guard management and QA endpoints with a shared-secret header.

    Uses a constant-time comparison so the check does not leak the secret
    through timing.
    """
    settings = get_settings()
    if not hmac.compare_digest(x_management_secret, settings.management_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing management secret.",
        )
