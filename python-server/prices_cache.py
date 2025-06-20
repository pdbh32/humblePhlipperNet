import time
import threading
from collections import OrderedDict

import wiki_api
import config

_cache = {
    "5m": OrderedDict(),   # key = timestamp, value = {"data": ..., "fetched_at": ..., "data_timestamp": ...}
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

def get_5m_data(t=-1):
    return _get_time_bucketed_data("5m", t=t, interval_seconds=300)

def get_1h_data(t=-1):
    return _get_time_bucketed_data("1h", t=t, interval_seconds=3600)

def get_latest_data():
    return _get_simple_ttl_data("latest", ttl_seconds=30)

def get_mapping_data():
    return _get_simple_ttl_data("mapping", ttl_seconds=7200)

def _get_time_bucketed_data(key, t, interval_seconds):
    bucket_timestamp = ((int(time.time() - config.WIKI_REQUEST_OFFSET_SECONDS) // interval_seconds) + t) * interval_seconds
    with _locks[key]:
        if bucket_timestamp not in _cache[key]:
            # fetch and insert
            entry = wiki_api.fetch(f"/{key}", timestamp=bucket_timestamp)
            _cache[key][bucket_timestamp] = entry

            # trim to most recent MAX_BUCKETS
            while len(_cache[key]) > config.MAX_BUCKETS:
                _cache[key].popitem(last=False)

        return _cache[key][bucket_timestamp]["data"]

def _get_simple_ttl_data(key, ttl_seconds):
    with _locks[key]:
        if time.time() - _cache[key]["fetched_at"] > ttl_seconds:
            _cache[key] = wiki_api.fetch(f"/{key}")
        return _cache[key]["data"]
