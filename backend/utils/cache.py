"""Simple cache interface.

In development the in-memory backend is used.  Swap for Redis by setting
REDIS_URL and instantiating RedisCacheBackend instead.
"""

import json
from abc import ABC, abstractmethod
from typing import Any

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class CacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None: ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...


class InMemoryCache(CacheBackend):
    """Thread-unsafe in-memory cache — suitable for single-worker development."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Any | None:
        return self._store.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        # TTL is intentionally ignored for the in-memory backend
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


# TODO: implement RedisCacheBackend using aioredis when REDIS_URL is configured
# class RedisCacheBackend(CacheBackend): ...

_cache: CacheBackend = InMemoryCache()


def get_cache() -> CacheBackend:
    return _cache
