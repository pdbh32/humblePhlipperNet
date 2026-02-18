from __future__ import annotations

import random
import time
import threading
import traceback
from typing import Callable

from humblePhlipperPython.config import settings
from humblePhlipperPython.config.runtime import SESSION_TIMESTAMP
from humblePhlipperPython.caches import market_data as wiki_cache, quotes as quotes_cache
from humblePhlipperPython.storage import market_data as wiki_storage, events as events_storage
from humblePhlipperPython.integrations import wiki, discord
from humblePhlipperPython.utils import profit_calculator
from humblePhlipperPython.core.base import BaseQuoteModel
from humblePhlipperPython.core.EWMA.model import EWMAQuoteModel

WIKI_REQ_OFFSET_SECS = random.randint(5,20) # Offset requests by a random number of seconds (e.g., WIKI_REQ_OFFSET_SEC = 7: 13:45:00 - > 13:45:07)

T_5M = 12 * 24 * 7                          # Cache the last 24 hours of 5m series data
T_1H = 24 * 7                               # Cache the last 24 hours of 1h series data
T_LATEST = 5                                # Cache the most recent latest data
T_MAPPING = 1                               # Cache the most recent mapping data

INT_SECS_5M = 60 * 5                        # Fetch, cache, and save 5m series data every 5 minutes
INT_SECS_1H = 60 * 60                       # Fetch, cache, and save 1h series data every 1 hour
INT_SECS_LATEST = 60                        # Fetch, cache, and save latest data every 30 seconds
INT_SECS_MAPPING = 60 * 60 * 2              # Fetch, cache, and save mapping data every 2 hours

def _load_quote_model() -> BaseQuoteModel:
    configured_model = settings.MODEL.lower()
    if configured_model == "ewma":
        return EWMAQuoteModel()
    # if configured_model == "kf":
        # return KFQuoteModel()
    raise ValueError(f"Unsupported settings.MODEL={settings.MODEL!r}. Supported values: 'ewma', 'kf'.")

QUOTE_MODEL = _load_quote_model()

def _ingest_wiki_data(endpoint: str, timestamp: int) -> None:
    if wiki_storage.get_path(endpoint, timestamp).exists(): return wiki_storage.load(endpoint, timestamp)
    return wiki.fetch(endpoint, timestamp)

def _update_wiki_cache(endpoint: str, int_secs: int, T: int) -> None:
    existing_ts = wiki_cache.get(endpoint).keys()
    required_ts = [int(time.time() // int_secs - t) * int_secs for t in range(T, 0, -1)] if endpoint in ["5m", "1h"] else (sorted(existing_ts)[-(T-1):] if T > 1 else []) + [int(time.time())]
    stale_ts    = [ts for ts in existing_ts if ts not in required_ts]
    missing_ts  = [ts for ts in required_ts if ts not in existing_ts]
    new_entries = {ts: _ingest_wiki_data(f"{endpoint}", timestamp=ts) for ts in missing_ts}

    for ts in stale_ts:
        wiki_cache.pop(endpoint, ts)
    for ts in missing_ts:
        wiki_cache.set(endpoint, new_entries[ts]["timestamp"], new_entries[ts])
        if endpoint != "mapping":
            wiki_storage.save(new_entries[ts])

def _init_quotes_cache() -> None:
    five_m = wiki_cache.get_df("5m")
    one_h = wiki_cache.get_df("1h")
    latest = wiki_cache.get_df("latest")
    quotes = QUOTE_MODEL.train(five_m, one_h, latest)
    quotes_cache.update(quotes)

def _update_quotes_cache() -> None:
    five_m = wiki_cache.get_df("5m")
    one_h = wiki_cache.get_df("1h")
    latest = wiki_cache.get_df("latest")
    quotes = QUOTE_MODEL.update(five_m, one_h, latest)
    quotes_cache.update(quotes)

def _send_discord_notification() -> None:
    event_list_map = events_storage.load_all(SESSION_TIMESTAMP)
    num_users = len(event_list_map)
    total_profit = sum(profit_calculator.get_total_profit(event_list) for event_list in event_list_map.values())
    combined_runtime_secs = sum(event_list[-1].timestamp - event_list[0].timestamp for event_list in event_list_map.values() if len(event_list) > 1)
    session_runtime_sec = int(time.time() - SESSION_TIMESTAMP)
    discord.send(num_users, total_profit, combined_runtime_secs, session_runtime_sec)

def _5m() -> None:
    _update_wiki_cache("5m", INT_SECS_5M, T_5M)
    _update_quotes_cache()

def _1h() -> None:
    _update_wiki_cache("1h", INT_SECS_1H, T_1H)
    # _update_quotes_cache()
    _send_discord_notification()

def _latest() -> None:
    _update_wiki_cache("latest", INT_SECS_LATEST, T_LATEST)
    # _update_quotes_cache()

def _mapping() -> None:
    _update_wiki_cache("mapping", INT_SECS_MAPPING, T_MAPPING)

def init() -> list[threading.Thread]:
    _update_wiki_cache("5m", INT_SECS_5M, T_5M)
    _update_wiki_cache("1h", INT_SECS_1H, T_1H)
    _update_wiki_cache("latest", INT_SECS_LATEST, T_LATEST)
    _update_wiki_cache("mapping", INT_SECS_MAPPING, T_MAPPING)
    _init_quotes_cache()
    tasks = [
        (_5m, INT_SECS_5M, WIKI_REQ_OFFSET_SECS),
        (_1h, INT_SECS_1H, WIKI_REQ_OFFSET_SECS),
        (_latest, INT_SECS_LATEST, WIKI_REQ_OFFSET_SECS),
        (_mapping, INT_SECS_MAPPING, WIKI_REQ_OFFSET_SECS),
    ]
    threads = []
    for func, int_secs, offset, in tasks:
        thread = _make_thread(func, int_secs, offset)
        thread.start()
        threads.append(thread)
    return threads

def _run_periodic(func: Callable[[], None], int_secs: int, offset: int) -> None:
    next_run = (time.time() // int_secs + 1) * int_secs + offset
    time.sleep(max(0, next_run - time.time()))
    while True:
        try:
            func()
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            traceback.print_exc()

        next_run += int_secs
        sleep_secs = next_run - time.time()
        if sleep_secs > 0:
            time.sleep(sleep_secs)
        else:
            next_run = (time.time() // int_secs) * int_secs + offset

def _make_thread(func: Callable[[], None], int_secs: int, offset: int) -> threading.Thread:
    thread = threading.Thread(
        target=_run_periodic,
        args=(func, int_secs, offset),
        daemon=True,
    )
    return thread