"""Thread-safe LRU Cache with TTL and async eviction — hardened by SAGE-PRO."""
import asyncio
import threading
import time
from collections import OrderedDict
from typing import Any, Optional


class AsyncTTLCache:
    """A thread-safe LRU cache with per-key TTL and background async eviction.

    Design rationale (SAGE-PRO Architect):
        - OrderedDict gives O(1) move-to-end for LRU ordering.
        - A dedicated asyncio task performs periodic sweeps instead of
          checking expiry on every read (amortised cost).
        - threading.Lock protects the dict so sync callers are safe too.
    """

    def __init__(self, maxsize: int = 128, default_ttl: float = 60.0,
                 eviction_interval: float = 5.0) -> None:
        self._maxsize = maxsize
        self._default_ttl = default_ttl
        self._eviction_interval = eviction_interval
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._eviction_task: Optional[asyncio.Task[None]] = None

    # ── public API ───────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        """Return value for *key* or None if missing / expired."""
        with self._lock:
            if key not in self._store:
                return None
            value, expires = self._store[key]
            if time.monotonic() > expires:
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return value

    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Insert or update *key*.  Evicts LRU entry when full."""
        ttl = ttl if ttl is not None else self._default_ttl
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, time.monotonic() + ttl)
            if len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    @property
    def size(self) -> int:
        return len(self._store)

    # ── async eviction ───────────────────────────────────────────────

    async def start_eviction(self) -> None:
        """Launch the background eviction loop."""
        self._eviction_task = asyncio.create_task(self._evict_loop())

    async def stop_eviction(self) -> None:
        if self._eviction_task:
            self._eviction_task.cancel()
            try:
                await self._eviction_task
            except asyncio.CancelledError:
                pass

    async def _evict_loop(self) -> None:
        while True:
            await asyncio.sleep(self._eviction_interval)
            now = time.monotonic()
            with self._lock:
                expired = [k for k, (_, exp) in self._store.items() if now > exp]
                for k in expired:
                    del self._store[k]
