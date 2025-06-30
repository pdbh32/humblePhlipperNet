import threading
import time
import numpy as np

import wiki_cache
import osrs_constants
import models
import tax

TTL_SECONDS = 20

_cache = {
    "prices": {"data": {}, "compiled_at": 0},
    "order": {"data": [], "compiled_at": 0}
}

_locks = {
    "prices": threading.Lock(),
    "order": threading.Lock()
}

def get_prices() -> dict[int, dict[str, int]]:
    """
    Return cached bid/ask prices, refreshing if stale.
    """
    now = time.time()
    with _locks["prices"]:
        if now - _cache["prices"]["compiled_at"] > TTL_SECONDS:
            prices, _ = _compute_prices_and_order("5m", 12)
            _cache["prices"]["data"] = prices
            _cache["prices"]["compiled_at"] = now
        return _cache["prices"]["data"]

def get_order() -> list[int]:
    """
    Return cached order list, refreshing if stale.
    """
    now = time.time()
    with _locks["order"]:
        if now - _cache["order"]["compiled_at"] > TTL_SECONDS:
            _, order = _compute_prices_and_order("1h", 12)
            _cache["order"]["data"] = order
            _cache["order"]["compiled_at"] = now
        return _cache["order"]["data"]

def _compute_prices_and_order(series: str, T: int) -> tuple[dict, list[int]]:
    fetch_fn = {'5m': wiki_cache.get_5m_data, '1h': wiki_cache.get_1h_data}[series]
    series_by_id = {}

    for i in reversed(range(1, T + 1)):
        for item_id, period_data in fetch_fn(t=-i).items():
            series_by_id.setdefault(item_id, []).append(period_data)

    latest = wiki_cache.get_latest_data()
    prices, order_criteria = {}, {}

    for item_id, timeseries in series_by_id.items():
        tradeList = models.TradeList() # treat data as a synthetic list of "trades" to calculate "profit"
        bid_prices, ask_prices, bid_vols, ask_vols = [], [], [], []

        for period_data in timeseries:
            bid_price = period_data.get("avgLowPrice") or np.nan
            ask_price = period_data.get("avgHighPrice") or np.nan
            bid_vol = period_data.get("lowPriceVolume") or 0
            ask_vol = period_data.get("highPriceVolume") or 0

            if not np.isnan(bid_price):
                tradeList.increment(models.Trade(timestamp=0, itemId=0, itemName="", price=bid_price, quantity=bid_vol))
            if not np.isnan(ask_price):
                tradeList.increment(models.Trade(timestamp=0, itemId=0, itemName="", price=ask_price, quantity=-1*ask_vol))

            bid_prices.append(bid_price)
            ask_prices.append(ask_price)
            bid_vols.append(bid_vol)
            ask_vols.append(ask_vol)

        bid_prices = np.array(bid_prices, dtype=float)
        ask_prices = np.array(ask_prices, dtype=float)
        bid_vols = np.array(bid_vols, dtype=float)
        ask_vols = np.array(ask_vols, dtype=float)

        if not np.all(np.isnan(bid_prices)) and not np.all(np.isnan(ask_prices)):
            bid = vwma(bid_prices, bid_vols)
            ask = vwma(ask_prices, ask_vols)

            prices[item_id] = {
                "bid": max(round(bid), 1),
                "ask": min(round(ask), osrs_constants.MAX_CASH)
            }
            order_criteria[item_id] = {
                "avg_pre_tax_margin": np.nanmean(ask_prices) - np.nanmean(bid_prices),
                "latest_post_tax_margin": tax.get_post_tax_price(item_id, latest[item_id]["high"]) - latest[item_id]["low"],
                "profit": models.TradeList._get_item_sublist_profit(tradeList)
            }

    MIN_AVG_PRE_TAX_MARGIN = 2
    MIN_LATEST_POST_TAX_MARGIN = 1
    
    order = sorted(
        prices,
        key=lambda item_id: (
            order_criteria[item_id]["avg_pre_tax_margin"] < MIN_AVG_PRE_TAX_MARGIN,
            order_criteria[item_id]["latest_post_tax_margin"] < MIN_LATEST_POST_TAX_MARGIN,
            -order_criteria[item_id]["profit"]
        )
    )
    return prices, order

def vwma(prices: np.ndarray, volumes: np.ndarray) -> float:
    valid = ~np.isnan(prices)
    if not np.any(valid):
        return np.nan
    return np.sum(prices[valid] * volumes[valid]) / np.sum(volumes[valid])
