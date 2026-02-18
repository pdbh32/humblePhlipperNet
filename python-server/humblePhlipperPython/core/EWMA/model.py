from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from humblePhlipperPython.schemata.domain.quote import Quote
from humblePhlipperPython.core.base import BaseQuoteModel
from humblePhlipperPython.utils import tax, osrs_constants

@dataclass(frozen=True)
class Model:
    mid_value: float
    spread_value: float
    e_bid_fill: Callable[[float], float]  # bid price -> expected quantity
    e_ask_fill: Callable[[float], float]  # ask price -> expected quantity

def _build_item_model(item_df: pd.DataFrame, span: int = 12) -> Model:
    g = item_df.sort_index()
    low, high = g["avg_low_price"].astype(float), g["avg_high_price"].astype(float)
    # low = low.clip(lower=low.quantile(0.01), upper=low.quantile(0.99))
    # high = high.clip(lower=high.quantile(0.01), upper=high.quantile(0.99))
    s = low.dropna();  n = s.size
    if n: low = low.clip(lower=s.nsmallest(min(n, max(1, int(np.ceil(0.01*n))))).iloc[-1])
    s = high.dropna(); n = s.size
    if n: high = high.clip(upper=s.nlargest(min(n, max(1, int(np.ceil(0.01*n))))).iloc[-1])
    el, eh = low.ewm(span=span, adjust=False).mean().round(), high.ewm(span=span, adjust=False).mean().round()
    mid, spr = float(0.5 * (el.iat[-1] + eh.iat[-1])), float(eh.iat[-1] - el.iat[-1])
    dl, dh = (low - el).to_numpy(float), (high - eh).to_numpy(float)
    dl, dh = np.sort(dl[np.isfinite(dl)]), np.sort(dh[np.isfinite(dh)])
    Fl = (lambda z: float(np.searchsorted(dl, z, "left") / max(dl.size, 1)))   # strict CDF
    Fh = (lambda z: float(np.searchsorted(dh, z, "right") / max(dh.size, 1)))  # weak CDF
    vb = float(g["low_price_volume"].astype(float).ewm(span=span, adjust=False).mean().iat[-1])
    va = float(g["high_price_volume"].astype(float).ewm(span=span, adjust=False).mean().iat[-1])
    low_hat, high_hat = mid - 0.5 * spr, mid + 0.5 * spr
    return Model(
        mid_value=mid if mid > 0 else 0.0,
        spread_value=spr if spr > 0 else 0.0,
        e_bid_fill=lambda b: vb * Fl(float(b) - low_hat),
        e_ask_fill=lambda a: va * (1.0 - Fh(float(a) - high_hat)),
    )

def _profit(quote: Quote) -> float:
    return (tax.get_post_tax_price(quote.ask_price, quote.item_id) - quote.bid_price) * min(quote.bid_quantity, quote.ask_quantity)

def _item_quote(item_id: int, item_df: pd.DataFrame) -> Quote:
    model = _build_item_model(item_df)

    best_quote = None
    for k in np.arange(1.0, 0.0, -0.1):
        bid_price = max(round(model.mid_value - k * model.spread_value), 1)
        ask_price = min(round(model.mid_value + k * model.spread_value), osrs_constants.MAX_INT)
        if ask_price % (1/osrs_constants.GE_TAX_RATE) == 0: ask_price -= 1 
        quote = Quote(
            item_id=item_id,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_quantity=model.e_bid_fill(bid_price),
            ask_quantity=model.e_ask_fill(ask_price),
        )
        if best_quote is None or _profit(quote) > _profit(best_quote):
            best_quote = quote

    return best_quote

class EWMAQuoteModel(BaseQuoteModel):
    def _build(self, five_m: pd.DataFrame) -> dict[int, Quote]:
        return {
            item_id: _item_quote(item_id, item_df)
            for item_id, item_df in five_m.groupby("item_id")
            if item_df["avg_high_price"].notna().any() and item_df["avg_low_price"].notna().any()
        }

    def train(self, five_m: pd.DataFrame, one_h: pd.DataFrame, latest: pd.DataFrame) -> dict[int, Quote]:
        return self._build(five_m)

    def update(self, five_m: pd.DataFrame, one_h: pd.DataFrame, latest: pd.DataFrame) -> dict[int, Quote]:
        return self._build(five_m)
