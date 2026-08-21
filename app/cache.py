from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import redis.asyncio as redis

from app.config import REDIS_URL, REDIS_CACHE_TTL

logger = logging.getLogger(__name__)
KEY_PREFIX = "llm_cache"


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0

    @property
    def total(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return (self.hits / self.total * 100) if self.total else 0.0


class RedisCache:

    def __init__(self, url: str = REDIS_URL, default_ttl: int = REDIS_CACHE_TTL):
        self._url = url
        self._default_ttl = default_ttl
        self._client: Optional[redis.Redis] = None
        self._stats = CacheStats()
        self._connected = False

    async def connect(self) -> None:
        try:
            self._client = redis.from_url(
                self._url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            await self._client.ping()
            self._connected = True
            logger.info("Redis cache connected → %s", self._url)
        except Exception:
            self._connected = False
            logger.warning("Redis unavailable — LLM cache disabled", exc_info=True)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._connected = False
            logger.info("Redis cache connection closed")

    @property
    def is_connected(self) -> bool:
        return self._connected

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().split())

    @classmethod
    def _make_key(cls, question: str, tenant: str) -> str:
        normalized = f"{cls._normalize(tenant)}::{cls._normalize(question)}"
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"{KEY_PREFIX}:{tenant}:{digest}"

    async def get(self, question: str, tenant: str) -> Optional[str]:
        if not self._connected:
            self._stats.misses += 1
            return None
        try:
            raw = await self._client.get(self._make_key(question, tenant))
            if raw is None:
                self._stats.misses += 1
                return None
            payload = json.loads(raw)
            self._stats.hits += 1
            logger.debug("Cache HIT  [%s] %s…", tenant, question[:60])
            return payload["answer"]
        except Exception:
            self._stats.misses += 1
            logger.warning("Redis GET failed — treating as cache miss", exc_info=True)
            return None

    async def set(
        self, question: str, tenant: str, answer: str, ttl: Optional[int] = None
    ) -> None:
        if not self._connected:
            return
        try:
            key = self._make_key(question, tenant)
            payload = json.dumps({
                "answer": answer,
                "tenant": tenant,
                "question_hash": hashlib.sha256(
                    self._normalize(question).encode()
                ).hexdigest(),
                "cached_at": time.time(),
            })
            await self._client.setex(key, ttl or self._default_ttl, payload)
            logger.debug("Cache SET  [%s] %s…", tenant, question[:60])
        except Exception:
            logger.warning("Redis SET failed — answer not cached", exc_info=True)

    async def invalidate_tenant(self, tenant: str) -> int:
        if not self._connected:
            return 0
        try:
            pattern = f"{KEY_PREFIX}:{tenant}:*"
            deleted = 0
            async for key in self._client.scan_iter(match=pattern, count=200):
                await self._client.delete(key)
                deleted += 1
            logger.info("Invalidated %d cached answers for tenant '%s'", deleted, tenant)
            return deleted
        except Exception:
            logger.warning("Redis SCAN/DELETE failed during invalidation", exc_info=True)
            return 0

    async def get_stats(self) -> dict:
        keys_count = 0
        if self._connected:
            try:
                async for _ in self._client.scan_iter(match=f"{KEY_PREFIX}:*", count=500):
                    keys_count += 1
            except Exception:
                pass
        return {
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "total": self._stats.total,
            "hit_rate_pct": round(self._stats.hit_rate, 2),
            "keys_count": keys_count,
            "connected": self._connected,
        }

cache = RedisCache()
