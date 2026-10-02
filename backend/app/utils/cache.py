import time
from collections import OrderedDict
from typing import Any


class TTLCache:
    """Tiny in-process TTL + LRU cache for external API responses.

    ponytail: per-process memory; swap for Redis if the backend runs as several replicas.
    """

    def __init__(self, ttl_seconds: float, maxsize: int = 512):
        self.ttl = ttl_seconds
        self.maxsize = maxsize
        self._data: OrderedDict[Any, tuple[float, Any]] = OrderedDict()

    def get(self, key):
        item = self._data.get(key)
        if item is None:
            return None
        expires, value = item
        if expires < time.monotonic():
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key, value, ttl: float | None = None) -> None:
        self._data[key] = (time.monotonic() + (self.ttl if ttl is None else ttl), value)
        self._data.move_to_end(key)
        while len(self._data) > self.maxsize:
            self._data.popitem(last=False)

    def clear(self) -> None:
        self._data.clear()
