from __future__ import annotations

import threading

from humblePhlipperPython.schemata.domain.four_hour_limit import FourHourLimit

_cache: dict[str, dict[int, FourHourLimit]] = {} # { user : { item_id : FourHourLimit } }
_lock = threading.RLock()

def get(user: str) -> dict[int, FourHourLimit]:
    with _lock:
        limits = _cache.get(user)
        return limits

def set(user: str, limits: dict[int, FourHourLimit]) -> None:
    with _lock:
        _cache[user] = limits
