from __future__ import annotations

import time
import requests

import pandas as pd
from pydantic import BaseModel

from humblePhlipperPython.config.settings import WIKI_REQ_HEADERS
from humblePhlipperPython.schemata.external.five_minute import FiveMinute
from humblePhlipperPython.schemata.external.one_hour import OneHour
from humblePhlipperPython.schemata.external.latest import Latest
from humblePhlipperPython.schemata.external.mapping import Mapping

BASE_URL = "https://prices.runescape.wiki/api/v1/osrs/"

_SESSION = requests.Session()

def _as_df(d: dict[int, BaseModel], ts: int) -> pd.DataFrame | None:
    return pd.DataFrame.from_records(
        ({**o.model_dump(), "item_id": item_id, "timestamp": ts}) for item_id, o in d.items()
        ).set_index(["item_id", "timestamp"]) if len(d) > 0 else None

def fetch(endpoint: str, timestamp: int | None = None) -> dict[str, object]:
    url = f"{BASE_URL}{endpoint}"
    params = {"timestamp": timestamp} if timestamp else {}
    response = _SESSION.get(url, headers=WIKI_REQ_HEADERS, params=params)
    response.raise_for_status()
    j = response.json()

    now = int(time.time())

    match endpoint:
        case "5m":
            return {
                "endpoint": endpoint,
                "timestamp": j.get("timestamp"),
                "data": _as_df({int(k): FiveMinute.model_validate(v) for k, v in j["data"].items()}, j.get("timestamp"))
            }
        case "1h":
            return {
                "endpoint": endpoint,
                "timestamp": j.get("timestamp"),
                "data": _as_df({int(k): OneHour.model_validate(v) for k, v in j["data"].items()}, j.get("timestamp"))
            }
        case "latest":
            return {
                "endpoint": endpoint,
                "timestamp": now,
                "data": _as_df({int(k): Latest.model_validate(v) for k, v in j["data"].items()}, now)
            }
        case "mapping":
            return {
                "endpoint": endpoint,
                "timestamp": now,
                "data": {d["id"]: Mapping.model_validate(d) for d in j}

            }