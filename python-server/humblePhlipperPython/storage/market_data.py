from __future__ import annotations

import pathlib

import datetime as dt
import pandas as pd
import portalocker

from humblePhlipperPython.utils.file_helpers import lock as lock
from humblePhlipperPython.config.paths import MARKET_DATA_DIR


def _dt(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime("%Y%m%d")

def _hour(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime("%H")

def get_path(endpoint: str, ts: int) -> pathlib.Path:
    return MARKET_DATA_DIR / endpoint / f"dt={_dt(ts)}" / f"hour={_hour(ts)}" / f"ts={ts}.parquet"

def load(endpoint: str, ts: int) -> pd.DataFrame:
    path = get_path(endpoint, ts)
    if not path.exists():
        data = None
    else:
        lock_path = path.with_suffix(path.suffix + ".lock")
        with lock(lock_path, "a", portalocker.LockFlags.SHARED):
            data = pd.read_parquet(path)
    return {"endpoint" : endpoint, "timestamp": ts, "data": data}

def save(entry: dict[str, object]) -> None:
    endpoint = entry["endpoint"]
    ts = entry["timestamp"]
    data = entry["data"]

    if data is None: return

    path = get_path(endpoint, ts) 
    lock_path = path.with_suffix(path.suffix + ".lock")
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with lock(lock_path, "a", portalocker.LockFlags.EXCLUSIVE):
        data.to_parquet(tmp_path, index=True)
        tmp_path.replace(path)