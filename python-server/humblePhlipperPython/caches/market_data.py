from __future__ import annotations

import threading
from collections import OrderedDict

import pandas as pd

_caches: dict[str, object] = {
    "5m": OrderedDict(),       # { timestamp : { "endpoint" : "5m",      "timestamp" : timestamp, "data" : None | pd.DataFrame(columns=["item_id", "timestamp", "avg_high_price", "high_price_volume", "avg_low_price", "low_price_volume"]) } }
    "1h": OrderedDict(),       # { timestamp : { "endpoint" : "1h",      "timestamp" : timestamp, "data" : None | pd.DataFrame(columns=["item_id", "timestamp", "avg_high_price", "high_price_volume", "avg_low_price", "low_price_volume"]) } }
    "latest": OrderedDict(),   # { timestamp : { "endpoint" : "latest",  "timestamp" : timestamp, "data" : None | pd.DataFrame(columns=["item_id", "timestamp", "high", "high_time", "low", "low_time"]) } }
    "mapping": OrderedDict()   # { timestamp : { "endpoint" : "mapping", "timestamp" : timestamp, "data" : None | { item_id : Mapping } } }
}
_locks: dict[str, threading.Lock] = {k: threading.Lock() for k in _caches.keys()}

def get(endpoint: str) -> dict[str, object]:
    with _locks[endpoint]:
        return _caches[endpoint]

def pop(endpoint: str, timestamp: int) -> None:
    with _locks[endpoint]:
        _caches[endpoint].pop(timestamp, None)

def set(endpoint: str, timestamp: int, entry: dict[str, object]) -> None:
    with _locks[endpoint]:
        _caches[endpoint][timestamp] = entry

def get_latest(endpoint: str) -> dict[str, object] | None:
    with _locks[endpoint]:
        return next(reversed(_caches[endpoint].values()), None)
    
def get_df(endpoint: str) -> pd.DataFrame:
    with _locks[endpoint]:
        df = pd.concat([v["data"] for v in _caches[endpoint].values() if v["data"] is not None]).sort_index()
        items = df.index.get_level_values("item_id").unique()
        times = list(_caches[endpoint].keys())
        df = df.reindex(pd.MultiIndex.from_product([items, times], names=["item_id", "timestamp"]))
        return df.fillna({"low_price_volume": 0, "high_price_volume": 0})