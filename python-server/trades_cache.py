import threading
import time

import config
import models

# { users: TradeList }
_cache: dict[str, models.TradeList] = {}

_lock = threading.Lock()

def update_with_trades(user : str, trades : list[dict]) -> None:
    """Update the cache with a user's trades."""
    with _lock:
        if user not in _cache:
            _cache[user] = models.TradeList()
        for trade in trades:
            if trade is not None:
                _cache[user].increment(models.Trade(**trade))

def get() -> models.TradeList:
    with _lock:
        return _cache.copy()