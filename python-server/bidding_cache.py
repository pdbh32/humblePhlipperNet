import threading
import time

import config

_lock = threading.Lock()
_active_bids = {}  # {itemId: {"user": ..., "timestamp": ...}}

def set_bid(item_id: int, user: str):
    with _lock:
        _active_bids[item_id] = {"user": user, "timestamp": time.time()}

def get_bid(item_id: int):
    with _lock:
        return _active_bids.get(item_id)

def clear_bid(item_id: int):
    with _lock:
        _active_bids.pop(item_id, None)

def is_being_bid(item_id: int):
    with _lock:
        stale_ids = [item_id for item_id, info in _active_bids.items() if time.time() - info["timestamp"] > config.MAX_BID_AGE_SECONDS]
        for item_id in stale_ids: _active_bids.pop(item_id)
        # return item_id in [item_id for item_id, info in _active_bids.items() if info["user"] != user]
        return item_id in _active_bids.keys()
