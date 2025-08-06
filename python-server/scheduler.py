import threading
import time
import traceback

import config
import wiki_cache
import statistics_cache
import discord_notification

def _run_periodic(func, int_secs, offset):
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

def init():
    threads = []
    tasks = [
        (wiki_cache.update_5m, 300, config.WIKI_REQ_OFFSET_SECS),
        (wiki_cache.update_1h, 3600, config.WIKI_REQ_OFFSET_SECS),
        (wiki_cache.update_latest, 30, config.WIKI_REQ_OFFSET_SECS),
        (wiki_cache.update_mapping, 7200, config.WIKI_REQ_OFFSET_SECS),
        (statistics_cache.update_5m, 300, config.WIKI_REQ_OFFSET_SECS + 10), # give some time for wiki_cache to update
        (statistics_cache.update_1h, 3600, config.WIKI_REQ_OFFSET_SECS + 10), # give some time for wiki_cache to update
        (discord_notification.send, 2600, 0)
    ]
    for func, interval, aligned, in tasks:
        thread = threading.Thread(
            target=_run_periodic,
            args=(func, interval, aligned),
            daemon=True,
        )
        thread.start()
        threads.append(thread)
    return threads