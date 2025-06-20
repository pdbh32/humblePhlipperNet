import threading, time

import config

_lock = threading.RLock()

# { item_id: { user: timestamp } }
_cache: dict[int, dict[str, float]] = {}

def add(item_id: int, user: str) -> None:
    """Add or refresh a user's bid on an item."""
    with _lock: _cache.setdefault(item_id, {})[user] = time.time()

def clear(item_id: int, user: str) -> None:
    """Remove a user's bid from an item."""
    with _lock:
        users = _cache.get(item_id)
        if users and user in users:
            users.pop(user)
            if not users:
                _cache.pop(item_id)

def contains(item_id: int) -> bool:
    """Return True if *any* user is bidding this item."""
    with _lock: return bool(_cache.get(item_id))

def is_first_bidder(item_id: int, user: str) -> bool:
    """True if *user* was the first (earliest-timestamp) bidder recorded for *item_id*."""
    with _lock:
        users = _cache.get(item_id)
        if not users: return True
        return min(users.items(), key=lambda kv: kv[1])[0] == user

def clear_stale() -> None:
    """Remove all users with stale bid timestamps."""
    now = time.time()
    stale: list[tuple[int, str]] = []
    with _lock:
        for item_id, users in _cache.items():
            for user, ts in users.items():
                if now - ts > config.MAX_BID_AGE_SECONDS:
                    stale.append((item_id, user))
    for item_id, user in stale:
        clear(item_id, user)

def sync_user(user: str, current_item_ids: set[int]) -> None:
    """Ensure the cache reflects only the items this user is actually bidding."""
    with _lock:
        # Drop stale items (things user was bidding, but isn't anymore)
        for item_id, users in list(_cache.items()):
            if user in users and item_id not in current_item_ids:
                clear(item_id, user)

        # Refresh timestamps for active bids
        now = time.time()
        for item_id in current_item_ids:
            _cache.setdefault(item_id, {})[user] = now