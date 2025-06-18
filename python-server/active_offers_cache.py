import logging
import threading, time
from collections import defaultdict

import config

logger = logging.getLogger(__name__)

_lock = threading.RLock()

_by_item: dict[int, dict] = {} # {item_id: {"user": str, "timestamp": float}}
_by_user: defaultdict[str, set[int]] = defaultdict(set) # {user: {item_id, …}}

def add(item_id: int, user: str):
    now = time.time()
    with _lock:
        _by_item[item_id] = {"user": user, "timestamp": now}
        _by_user[user].add(item_id)

def clear(item_id: int):
    with _lock:
        info = _by_item.pop(item_id, None)
        if info:
            u = info["user"]
            _by_user[u].discard(item_id)
            if not _by_user[u]:
                _by_user.pop(u, None)

def contains(item_id: int) -> bool:
    with _lock:
        return item_id in _by_item

def clear_stale():
    stale_ids = [item_id for item_id, info in _by_item.items() if time.time() - info["timestamp"] > config.MAX_BID_AGE_SECONDS]
    for item_id in stale_ids: clear(item_id)

def sync_user(user: str, current_item_ids: set[int]):
    with _lock:
        cached = _by_user.get(user, set()).copy()
        for item_id in cached - current_item_ids: clear(item_id) # RLock (Reentrant Lock) allows this
        for item_id in current_item_ids:
            _by_item[item_id] = {"user": user, "timestamp": time.time()}
            _by_user[user].add(item_id)