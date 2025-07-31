import time
import requests
import threading
from collections import OrderedDict

import config

BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"

_cache = {
    "5m": OrderedDict(),   # key = timestamp, value = {"data": {item_id: {"avgLowPrice": ..., "avgHighPrice": ..., "lowPriceVolume": ..., "highPriceVolume": ...}}, "fetched_at": ..., "data_timestamp": ...}
    "1h": OrderedDict(),
    "latest": {"data": None, "fetched_at": 0, "data_timestamp": None},
    "mapping": {"data": None, "fetched_at": 0, "data_timestamp": None},
}

_locks = {
    "5m": threading.Lock(),
    "1h": threading.Lock(),
    "latest": threading.Lock(),
    "mapping": threading.Lock()
}

def get_5m():
    with _locks["5m"]:
        return _cache["5m"].copy()

def get_1h():
    with _locks["1h"]:
        return _cache["1h"].copy()

def get_latest():
    with _locks["latest"]:
        return _cache["latest"].copy()

def get_mapping():
    with _locks["mapping"]:
        return _cache["mapping"].copy()

def update_5m():
    _update_time_bucketed_data("5m", 300)

def update_1h():
    _update_time_bucketed_data("1h", 3600)

def update_latest():
    _update_simple_ttl_data("latest", 20)

def update_mapping():
    _update_simple_ttl_data("mapping", 7200)

def init():
    update_5m()
    update_1h()
    update_latest()
    update_mapping()

def _update_time_bucketed_data(key, int_secs):
    with _locks[key]:
        existing_timestamps = _cache[key].keys()

    bucket_timestamps = [int(time.time() // int_secs - t) * int_secs for t in range(config.T, 0, -1)]
    stale_timestamps = [ts for ts in existing_timestamps if ts not in bucket_timestamps]
    missing_timestamps = [ts for ts in bucket_timestamps if ts not in existing_timestamps]
    new_entries = {ts: _fetch(f"/{key}", timestamp=ts) for ts in missing_timestamps}

    with _locks[key]:
        for ts in stale_timestamps:
            _cache[key].pop(ts, None)
        for ts in missing_timestamps:
            _cache[key][ts] = new_entries[ts]

def _update_simple_ttl_data(key, ttl_secs):
    with _locks[key]:
        if time.time() - _cache[key]["fetched_at"] < ttl_secs: 
            return
        
    entry = _fetch(f"/{key}") 

    with _locks[key]:
        _cache[key] = entry 

def _fetch(endpoint, timestamp=None):
    url = f"{BASE_URL}{endpoint}"
    params = {"timestamp": timestamp} if timestamp else {}
    response = requests.get(url, headers=config.WIKI_REQ_HEADERS, params=params)
    response.raise_for_status()
    j = response.json()

    now = time.time()

    match endpoint:
        case "/5m" | "/1h":
            return {
                "data": {int(k): v for k, v in j["data"].items()},
                "fetched_at": now,
                "data_timestamp": j.get("timestamp")
            }
        case "/latest":
            return {
                "data": {int(k): v for k, v in j["data"].items()},
                "fetched_at": now,
                "data_timestamp": None
            }
        case "/mapping":
            return {
                "data": {d['id']: d for d in j},
                "fetched_at": now,
                "data_timestamp": None
            }
