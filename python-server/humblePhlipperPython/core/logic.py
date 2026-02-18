from __future__ import annotations

import time

import pandas as pd

from humblePhlipperPython.config import settings
from humblePhlipperPython.schemata.domain.offer import Offer, Status as OfferStatus
from humblePhlipperPython.schemata.domain.inventory_item import InventoryItem
from humblePhlipperPython.schemata.domain.four_hour_limit import FourHourLimit
from humblePhlipperPython.schemata.domain.quote import Quote
from humblePhlipperPython.schemata.domain.event import Event, Label as EventLabel
from humblePhlipperPython.schemata.external.mapping import Mapping
from humblePhlipperPython.utils import osrs_constants
from humblePhlipperPython.utils import tax

def _my_inventory_count(my_inventory: list[InventoryItem], item_id: int) -> int:
    return sum(item.quantity for item in my_inventory if item.item_id == item_id)

def _my_offers_contain(my_offers: list[Offer], item_id: int) -> bool:
    return any(o and o.item_id == item_id for o in my_offers)

def _others_offers_contain(others_offers: dict[str, list[Offer]], item_id: int) -> bool:
    return any(o and o.item_id == item_id for offers in others_offers.values() for o in offers)

def _others_inventories_contain(others_inventories: dict[str, list[InventoryItem]], item_id: int) -> bool:
    return any(i and i.item_id == item_id for inventories in others_inventories.values() for i in inventories)

def _no_bid_priority(others_offers: dict[str, list[Offer]], item_id: int, user: str) -> bool:
    return (
        any(hash(u) < hash(user) for u, offers in others_offers.items() if any(o and o.item_id == item_id for o in offers))             # another user with a lower hash (priority) is offering this item
        or any(o.item_id == item_id and o.status == OfferStatus.SELL for offers in others_offers.values() for o in offers)              # another user is trying to sell this item
    )

def _margin(item_id, bid_price: int, ask_price: int) -> float:
    return tax.get_post_tax_price(ask_price, item_id) - bid_price

def _profit_rate(quote: Quote) -> float:
    return _margin(quote.item_id, quote.bid_price, quote.ask_price) * min(quote.bid_quantity, quote.ask_quantity)

def _ask_revenue(quote: Quote) -> float:
    return tax.get_post_tax_price(quote.ask_price, quote.item_id) * quote.ask_quantity

def _empty_slot_available(my_offers: list[Offer], members_days_left: int) -> bool:
    return any(o is not None and o.status in (None, OfferStatus.EMPTY) and o.slot_index in (osrs_constants.P2P_OFFER_SLOTS if members_days_left > 0 else osrs_constants.F2P_OFFER_SLOTS) for o in my_offers)

def select_next_command(
        my_offers: list[Offer],                                          # user's current offers
        my_inventory: list[InventoryItem],                               # user's current inventory
        user: str,                                                       # user      
        members_days_left: int,                                          # days of OSRS membership remaining
        trade_restricted: bool,                                          # 20 hour / 10 qp / 100 ttl trade restriction status
        limits: dict[int, FourHourLimit],                                # item to four hour limits
        others_offers: dict[str, list[Offer]],                           # user to list of current offers for all other users
        others_inventories: dict[str, list[InventoryItem]],              # user to list of current inventories for all other users
        base_quotes: dict[int, Quote],                                   # item ID to current optimal prices and corresponding expected fills
        mappings: dict[int, Mapping],                                    # item ID to mapping info from OSRS wiki
    ):

    my_quotes = make_my_quotes(my_offers, my_inventory, members_days_left, trade_restricted, limits, others_offers, others_inventories, base_quotes, mappings)
    bid_order = sort_items_for_bid(my_quotes, base_quotes)
    ask_order = sort_items_for_ask(my_quotes)

    return (
        check_cancel(my_offers, user, members_days_left, limits, others_offers, others_inventories, base_quotes, mappings, my_quotes, bid_order, ask_order)
        or check_collect(my_offers)
        or check_ask(my_quotes, ask_order, my_offers, members_days_left)
        or check_bond(my_quotes, my_inventory, my_offers, members_days_left)
        or check_bid(my_quotes, bid_order, my_offers, members_days_left)
        or Event(timestamp=int(time.time()), label=EventLabel.IDLE)
    )

def make_my_quotes(
        my_offers: list[Offer],
        my_inventory: list[InventoryItem],
        members_days_left: int,
        trade_restricted: bool, 
        limits: dict[int, FourHourLimit], 
        others_offers: dict[str, list[Offer]],
        others_inventories: dict[str, list[InventoryItem]],
        base_quotes: dict[int, Quote],
        mappings: dict[int, Mapping],
        cash: int | None = None # to eventually construct counterfactuals and properly assess opportunity cost in check_cancel
    ):

    cash = cash or _my_inventory_count(my_inventory, osrs_constants.COINS_ID)

    bid_restrictions = [
        lambda item_id: members_days_left == 0 and mappings[item_id].members,                                                                 # members-only item when user is not a member
        lambda item_id: limits.get(item_id, FourHourLimit()).remaining(mappings.get(item_id).limit or osrs_constants.MAX_INT) == 0,           # four-hour limit reached for this item
        lambda item_id: _my_offers_contain(my_offers, item_id),                                                                               # user already has an offer for this item
        lambda item_id: _others_offers_contain(others_offers, item_id),                                                                       # another user already has an offer for this item
        lambda item_id: _my_inventory_count(my_inventory, item_id) > 0,                                                                       # user already has this item in their inventory <- redundant with current setup as we ask before bidding
        lambda item_id: _others_inventories_contain(others_inventories, item_id),                                                             # another user already has this item in their inventory
        lambda item_id: item_id == osrs_constants.BOND_TRADEABLE_ID,                                                                          # don't flip bonds
        lambda item_id: trade_restricted and item_id in osrs_constants.TRADE_RESTRICTED_IDS                                                   # trade-restricted item when user is trade-restricted
    ]

    ask_restrictions = [
        lambda item_id: _my_inventory_count(my_inventory, item_id) == 0,                                                                      # user doesn't have any of the item in their inventory to sell
        lambda item_id: _my_offers_contain(my_offers, item_id),                                                                               # user already has an offer for this item 
        lambda item_id: item_id == osrs_constants.BOND_TRADEABLE_ID,                                                                          # don't flip bonds
        lambda item_id: trade_restricted and item_id in osrs_constants.TRADE_RESTRICTED_IDS                                                   # trade-restricted item when user is trade-restricted
    ]

    def my_bid_quantity(item_id, base_quote):
        if any(restriction(item_id) for restriction in bid_restrictions):
            return 0
        target = round(max(base_quote.bid_quantity, 1))                                                                                       # expected quantity at our bid price
        potential = limits.get(item_id, FourHourLimit()).remaining(mappings[item_id].limit or osrs_constants.MAX_INT)                         # remaining four hour limit
        affordable = 0 if base_quote.bid_price <= 0 else cash // base_quote.bid_price                                                         # quantity we can afford with our current cash
        maximum = osrs_constants.MAX_INT // base_quote.bid_price if base_quote.bid_price > 0 else osrs_constants.MAX_INT                      # maximum quantity allowed by GE restrictions 
        return min(target, potential, affordable, maximum)
    
    def my_ask_quantity(item_id):
        if any(restriction(item_id) for restriction in ask_restrictions):
            return 0
        return _my_inventory_count(my_inventory, item_id)

    return {
        item_id: Quote(
            item_id=item_id,
            bid_price=base_quote.bid_price,
            ask_price=base_quote.ask_price,
            bid_quantity=my_bid_quantity(item_id, base_quote),
            ask_quantity=my_ask_quantity(item_id),
        )
        for item_id, base_quote in base_quotes.items() if item_id in mappings.keys()
    }

def sort_items_for_bid(my_quotes: dict[int, Quote], base_quotes: dict[int, Quote]) -> list[int]:
    bid_sort = sorted(
        my_quotes.keys(),
        key=lambda item_id: _profit_rate(base_quotes.get(item_id)),
        reverse=True,
    )
    return [item_id for item_id in bid_sort if my_quotes.get(item_id).bid_quantity > 0]

def sort_items_for_ask(my_quotes: dict[int, Quote]) -> list[int]:
    ask_sort = sorted(
        my_quotes.keys(), 
        key=lambda item_id: _ask_revenue(my_quotes.get(item_id)),
        reverse=True
    )
    return [item_id for item_id in ask_sort if my_quotes.get(item_id).ask_quantity > 0]

def check_cancel(
        my_offers: list[Offer],
        user: str,
        members_days_left: int,
        limits: dict[int, FourHourLimit], 
        others_offers: dict[str, list[Offer]],
        others_inventories: dict[str, list[InventoryItem]],
        base_quotes: dict,
        mappings: dict[int, Mapping],
        my_quotes: dict,
        bid_order: list[int],
        ask_order: list[int]
    ) -> Event | None:

    criteria = [
        ('bid price mismatch',           lambda offer: offer.status == OfferStatus.BUY and (offer.price != my_quotes.get(offer.item_id).bid_price)),
        ('ask price mismatch',           lambda offer: offer.status == OfferStatus.SELL and (offer.price != my_quotes.get(offer.item_id).ask_price)),
        ('multiple offers by me',        lambda offer: offer.status == OfferStatus.BUY and any(o is not None and o.item_id == offer.item_id and o.slot_index != offer.slot_index for o in my_offers)),
        ('multiple asks by me',          lambda offer: offer.status == OfferStatus.SELL and any(o is not None and o.item_id == offer.item_id and o.slot_index != offer.slot_index and o.status == OfferStatus.SELL for o in my_offers)),
        ('offered by another with prio', lambda offer: offer.status == OfferStatus.BUY and _no_bid_priority(others_offers, offer.item_id, user)),
        ("in another's inventory",       lambda offer: offer.status == OfferStatus.BUY and _others_inventories_contain(others_inventories, offer.item_id)),
        ('unprofitable flip',            lambda offer: offer.status == OfferStatus.BUY and offer.item_id != osrs_constants.BOND_TRADEABLE_ID and _margin(offer.item_id, offer.price, my_quotes.get(offer.item_id).ask_price) <= 0),
        ('bid opportunity cost',         lambda offer: offer.status == OfferStatus.BUY and not _empty_slot_available(my_offers, members_days_left) and len(bid_order) > 0 and _profit_rate(base_quotes.get(offer.item_id)) < _profit_rate(base_quotes.get(bid_order[0]))),
        ('ask opportunity cost',         lambda offer: offer.status == OfferStatus.SELL and not _empty_slot_available(my_offers, members_days_left) and len(ask_order) > 0 and _ask_revenue(Quote(item_id=offer.item_id, ask_price=offer.price, ask_quantity=offer.quantity)) < _ask_revenue(my_quotes.get(ask_order[0]))),
        ('limit reached',                lambda offer: offer.status == OfferStatus.BUY and limits.get(offer.item_id, FourHourLimit()).remaining(mappings[offer.item_id].limit or osrs_constants.MAX_INT) == 0),
    ]

    for offer in my_offers:
        if offer is None or offer.status in (None, OfferStatus.EMPTY) or offer.ready_to_collect:
            continue
        for reason, rule in criteria:
            if rule(offer):
                return Event(
                    **{k: v for k, v in offer.model_dump().items() if k in Event.model_fields},
                    timestamp=int(time.time()),
                    label=EventLabel.CANCEL,
                    text=reason,
                )
    return None
    
def check_collect(offers: list[Offer]) -> Event | None:
    for offer in offers:
        if offer is None:
            continue
        if offer.status in (None, OfferStatus.EMPTY) or not offer.ready_to_collect: 
            continue
        return Event(
            **{k: v for k, v in offer.model_dump().items() if k in Event.model_fields},
            timestamp=int(time.time()),
            label=EventLabel.COLLECT
        )
    return None

def check_ask(my_quotes: dict[int, Quote], ask_order: list[int], offers: list[Offer], members_days_left: int) -> Event | None:
    if not _empty_slot_available(offers, members_days_left): 
        return None
    for item_id in ask_order:
        return Event(timestamp=int(time.time()), label=EventLabel.ASK, item_id=item_id, quantity=my_quotes[item_id].ask_quantity, price=my_quotes[item_id].ask_price)
    return None

def check_bond(
        my_quotes: dict,
        my_inventory: list[InventoryItem],
        my_offers: list[Offer],
        members_days_left: int,
    ):
    if members_days_left > settings.AUTO_BOND_DAYS: 
        return None
    if _my_inventory_count(my_inventory, osrs_constants.BOND_TRADEABLE_ID) > 0 or _my_inventory_count(my_inventory, osrs_constants.BOND_UNTRADEABLE_ID) > 0:
        return Event(timestamp=int(time.time()), label=EventLabel.BOND)
    quote = my_quotes.get(osrs_constants.BOND_TRADEABLE_ID)
    if (
        _empty_slot_available(my_offers, members_days_left)
        and quote is not None
        and not pd.isna(quote.bid_price)
        and _my_inventory_count(my_inventory, osrs_constants.COINS_ID) >= quote.bid_price
        and not _my_offers_contain(my_offers, osrs_constants.BOND_TRADEABLE_ID)
    ):
        return Event(timestamp=int(time.time()), label=EventLabel.BID, item_id=osrs_constants.BOND_TRADEABLE_ID, quantity=1, price=quote.bid_price)
    return None

def check_bid(my_quotes: dict[int, Quote], bid_order: list[int], my_offers: list[Offer], members_days_left: int) -> Event | None:
    if not _empty_slot_available(my_offers, members_days_left): 
        return None
    for item_id in bid_order:
        return Event(timestamp=int(time.time()), label=EventLabel.BID, item_id=item_id, quantity=my_quotes[item_id].bid_quantity, price=my_quotes[item_id].bid_price)
    return None