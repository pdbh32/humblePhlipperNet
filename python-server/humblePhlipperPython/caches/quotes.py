from __future__ import annotations
import threading

from humblePhlipperPython.schemata.domain.quote import Quote

_cache: dict[int, Quote] = {} # { item_id : Quote }
_lock = threading.RLock()

def update(quotes) -> None:
    global _cache
    with _lock:
        _cache = quotes                 

def get() -> dict[int, Quote]:
    with _lock:
        return _cache