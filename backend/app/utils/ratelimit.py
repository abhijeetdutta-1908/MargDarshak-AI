"""Sliding-window rate limiting as a FastAPI dependency.

ponytail: in-process memory, so limits are per backend replica; move to Redis if you scale out.
"""

import math
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import get_settings


def client_ip(request: Request) -> str:
    # nginx sets X-Real-IP. Only trust it behind the proxy (don't publish port 8000 in production).
    return request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")


class RateLimiter:
    def __init__(self, name: str, limit: int, window_seconds: float):
        self.name, self.limit, self.window = name, limit, window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.limit:
                retry = math.ceil(self.window - (now - q[0]))
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    f"Too many requests. Try again in {retry} seconds.",
                    headers={"Retry-After": str(retry)},
                )
            q.append(now)
            if len(self._hits) > 10_000:  # bound memory: forget idle keys
                for k in [k for k, v in self._hits.items() if not v][:5000]:
                    del self._hits[k]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def __call__(self, request: Request) -> None:
        if get_settings().rate_limit_enabled:
            self.hit(client_ip(request))


# Brute-force protection on auth; cost protection on the ML-heavy endpoints.
login_limit = RateLimiter("login", 10, 60)
register_limit = RateLimiter("register", 5, 60)
recommend_limit = RateLimiter("recommend", 30, 60)
generate_limit = RateLimiter("generate", 10, 60)
ALL = [login_limit, register_limit, recommend_limit, generate_limit]
