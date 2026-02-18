from __future__ import annotations

import threading

from cachetools import TTLCache

from humblePhlipperPython.schemata.api.next_command_request import NextCommandRequest

TTL_SECONDS = 60

_cache: TTLCache[str, NextCommandRequest] = TTLCache(maxsize=10_000, ttl=TTL_SECONDS)
_lock = threading.RLock()

def get() -> TTLCache[str, NextCommandRequest]:
    with _lock:
        return _cache

def set(user: str, request: NextCommandRequest) -> None:
    with _lock:
        _cache[user] = request

