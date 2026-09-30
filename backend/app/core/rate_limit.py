"""A minimal in-memory sliding-window rate limiter.

Deliberately not a distributed solution (Redis, etc.) — this is meant to
blunt basic brute-force attempts against a single-instance deployment,
not to be a production-grade rate limiter for a multi-instance one. Swap
it for something like slowapi + Redis if the API ever runs behind a load
balancer with multiple worker processes.
"""

import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request, status

from backend.app.core.config import get_settings

_WINDOW_SECONDS = 60
_buckets: dict[str, list[float]] = defaultdict(list)


def rate_limit(max_requests: int):
    def dependency(request: Request) -> None:
        settings = get_settings()
        if not settings.rate_limiting_enabled:
            return

        client_host = request.client.host if request.client else "unknown"
        key = f"{client_host}:{request.url.path}"
        now = time.monotonic()

        bucket = _buckets[key]
        bucket[:] = [timestamp for timestamp in bucket if now - timestamp < _WINDOW_SECONDS]

        if len(bucket) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again in a minute.",
            )
        bucket.append(now)

    return Depends(dependency)
