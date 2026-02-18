from __future__ import annotations

from humblePhlipperPython.schemata.domain.event import Event, Label as EventLabel
from humblePhlipperPython.utils import tax

def _item_sublist_profit(item_sublist: list[Event]) -> int:
    avg_buy_price = None
    avg_sell_price = None
    inventory = 0
    profit = 0

    for event in item_sublist:
        if event is None or event.label != EventLabel.TRADE : continue
        if event.quantity > 0: # buys are recorded as a positive quantity
            if inventory < 0 and avg_sell_price is not None:
                profit += (tax.get_post_tax_price(avg_sell_price, event.item_id) - event.price) * min(event.quantity, -1 * inventory)
            avg_buy_price = event.price if avg_buy_price is None else (event.quantity * event.price + inventory * avg_buy_price) // (event.quantity + inventory)
        elif event.quantity < 0: # sells are recorded as a negative quantity
            if inventory > 0 and avg_buy_price is not None:
                profit += (tax.get_post_tax_price(event.price, event.item_id) - avg_buy_price) * min(-1 * event.quantity, inventory)
            avg_sell_price = event.price if avg_sell_price is None else (event.quantity * event.price + inventory * avg_sell_price) // (event.quantity + inventory)
        inventory += event.quantity
        if inventory <= 0: avg_buy_price = None
        if inventory >= 0: avg_sell_price = None

    return profit

def split_by_name(event_list: list[Event]) -> dict[str,  list[Event]]:
    event_list_map: dict[str, list[Event]] = {}
    for event in event_list:
        if event is None: continue
        event_list_map.setdefault(event.item_name, []).append(event)
    return event_list_map

def get_item_name_profit_map(event_list: list[Event]) -> dict[str, int]:
    item_sublist_map = split_by_name(event_list)
    return {name: _item_sublist_profit(item_sublist) for name, item_sublist in item_sublist_map.items()}

def get_sorted_item_name_profit_list(event_list: list[Event]) -> list[tuple[str, int]]:
    return sorted(get_item_name_profit_map(event_list).items(), key=lambda kv: (-kv[1], kv[0]))

def get_total_profit(event_list: list[Event]) -> int:
    return sum(get_item_name_profit_map(event_list).values())