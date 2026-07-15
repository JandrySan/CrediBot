import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Límite por proceso para proteger desarrollo y una única tarea ECS."""

    def __init__(self):
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int = 60) -> None:
        if limit <= 0:
            return

        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Demasiadas solicitudes. Intenta nuevamente en un minuto.",
                )
            timestamps.append(now)


limiter = InMemoryRateLimiter()


def rate_limit(scope: str, requests_per_minute: int):
    def dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        limiter.check(f"{scope}:{client_host}", requests_per_minute)

    return dependency
