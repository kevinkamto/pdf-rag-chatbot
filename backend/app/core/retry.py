"""A small async retry decorator for transient external-call failures."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def async_retry(
    *,
    attempts: int = 3,
    base_delay: float = 0.2,
    exceptions: tuple[type[BaseException], ...],
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Retry an async function on the given exceptions with exponential backoff.

    Intended for idempotent network calls (the Qdrant connection occasionally
    drops the first request). The final failure is re-raised unchanged.
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_error: BaseException | None = None
            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_error = exc
                    if attempt < attempts - 1:
                        await asyncio.sleep(base_delay * (2**attempt))
                        logger.warning(
                            "event=retry func=%s attempt=%s error=%s",
                            func.__name__,
                            attempt + 1,
                            type(exc).__name__,
                        )
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator
