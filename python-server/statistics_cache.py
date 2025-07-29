import threading
import numpy as np
import pandas as pd

import wiki_cache
import models

_cache = {
    "5m": None,
    "1h": None
}

_locks = {
    "5m": threading.Lock(),
    "1h": threading.Lock()
}

def get_5m():
    with _locks["5m"]:
        return _cache["5m"].copy()

def get_1h():
    with _locks["1h"]:
        return _cache["1h"].copy()
    
def update_5m():
    _update_statistics("5m")

def update_1h():
    _update_statistics("1h")

def init():
    update_5m()
    update_1h()

def _tabulate_wiki_cache(series: str) -> pd.DataFrame:
    mapping_cache = wiki_cache.get_mapping()
    price_cache = {'5m': wiki_cache.get_5m, '1h': wiki_cache.get_1h}[series]()

    records = []
    for ts, entry in price_cache.items():
        for item_id in mapping_cache["data"].keys():
            records.append({
                "timestamp": ts,
                "item_id": item_id,
                "avgHighPrice": entry["data"].get(item_id, {}).get("avgHighPrice", np.nan),
                "avgLowPrice":  entry["data"].get(item_id, {}).get("avgLowPrice",  np.nan),
                "highPriceVolume": entry["data"].get(item_id, {}).get("highPriceVolume", 0),
                "lowPriceVolume":  entry["data"].get(item_id, {}).get("lowPriceVolume",  0),
            })

    return pd.DataFrame.from_records(records).set_index(["item_id", "timestamp"]).sort_index()

def _simulate_profit(df):
    tradeList = models.TradeList()
    for bid_price, bid_vol, ask_price, ask_vol in zip(df["avgLowPrice"], df["lowPriceVolume"], df["avgHighPrice"], df["highPriceVolume"]):
        if not np.isnan(bid_price):
            tradeList.increment(models.Trade(timestamp=0, itemId=0, itemName="", price=bid_price, quantity=bid_vol))
        if not np.isnan(ask_price):
            tradeList.increment(models.Trade(timestamp=0, itemId=0, itemName="", price=ask_price, quantity=-1*ask_vol))
    return models.TradeList._get_item_sublist_profit(tradeList)

def _update_statistics(key: str):
    df = _tabulate_wiki_cache(key)
    gb = df.groupby("item_id")

    vol_bid = gb["lowPriceVolume"].sum()
    vol_ask = gb["highPriceVolume"].sum()

    mean_bid = gb["avgLowPrice"].mean()
    mean_ask = gb["avgHighPrice"].mean()

    sum_bid_pv = (df["avgLowPrice"]  * df["lowPriceVolume"]).groupby("item_id").sum()
    sum_ask_pv = (df["avgHighPrice"] * df["highPriceVolume"]).groupby("item_id").sum()
    vwap_bid = sum_bid_pv.div(vol_bid).where(vol_bid > 0, np.nan)
    vwap_ask = sum_ask_pv.div(vol_ask).where(vol_ask > 0, np.nan)

    std_bid = gb.avgLowPrice.std() 
    std_ask = gb.avgHighPrice.std()

    profit = gb.apply(_simulate_profit)

    stats = {
        item: {
            "profit":   profit[item],
            "vwap_bid": vwap_bid[item],
            "vwap_ask": vwap_ask[item],
            "mean_bid": mean_bid[item],
            "mean_ask": mean_ask[item],
            "vol_bid":  vol_bid[item],
            "vol_ask":  vol_ask[item],
            "std_bid":  std_bid[item],
            "std_ask":  std_ask[item],
        }
        for item in df.index.get_level_values("item_id")
    }

    with _locks[key]:
        _cache[key] = stats 