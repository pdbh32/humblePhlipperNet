import math
import pandas as pd

import active_offers_cache
import wiki_cache
import osrs_constants
import config
import models
import four_hour_limits
import tax
import statistics_cache

# ------------------------------
# Next Action Logic
# ------------------------------

def getActionData(actionRequest: models.ActionRequest):
    """
    Determine the next action for the bot based on current state.

    Parameters
    ----------
    actionRequest : models.ActionRequest
        Request wrapper containing the instance's portfolio, username, membership days left, and trade restricted status.

    Returns
    -------
    models.ActionData
        Action object specifying what to do next (e.g., BID, ASK, CANCEL, etc.).
    """
    portfolio = actionRequest.portfolio
    user = actionRequest.user
    members_days_left = actionRequest.membersDaysLeft
    trade_restricted = actionRequest.tradeRestricted

    update_active_offers(portfolio, user)

    biddables = get_biddables(user, members_days_left, trade_restricted)
    askables = get_askables(portfolio, members_days_left, trade_restricted)

    stats_5m = statistics_cache.get_5m() 
    stats_1h = statistics_cache.get_1h()

    prices = {
        item_id: {
            "bid": None if pd.isna(stats["vwap_bid"]) else int(stats["vwap_bid"].round()),
            "ask": None if pd.isna(stats["vwap_ask"]) else int(stats["vwap_ask"].round())
        }
        for item_id, stats in stats_5m.items()
    }
    order = sorted(
        [item_id for item_id in stats_1h.keys()],
        key=lambda item_id: (
            stats_1h[item_id]["mean_ask"] - stats_1h[item_id]["mean_bid"] < 2,
            -stats_1h[item_id]["profit"]
        )
    )

    return (
        check_cancel(portfolio, prices, user)
        or check_collect(portfolio)
        or check_ask(portfolio, prices, askables, members_days_left)
        or check_bond(portfolio, prices, members_days_left)
        or check_bid(portfolio, prices, order, biddables, members_days_left, user)
        or models.ActionData(action=models.ActionEnum.IDLE) # default action if no other conditions are met
    )

def update_active_offers(portfolio: models.Portfolio, user: str) -> None:
    """
    Sync active offers in cache with current portfolio state.

    Parameters
    ----------
    portfolio : models.Portfolio
        Instance's portfolio object.
    user : str
        Instance's identifier (username).
    """
    active_offers_cache.clear_stale()
    active_ids = {offer.itemId for offer in portfolio.offerList if offer.status not in (None, models.OfferStatus.EMPTY)}
    active_offers_cache.sync_user(user, active_ids)

def check_cancel(portfolio: models.Portfolio, prices: dict, user: str) -> models.ActionData | None:
    """
    Evaluate if any current offers should be canceled.

    Parameters
    ----------
    portfolio : models.Portfolio
        Instance's portfolio.
    prices : dict
        Current market prices.
    user : str
        Instance's identifier (username).

    Returns
    -------
    models.ActionData or None
        Action to cancel an offer, or None if no cancellation is needed.
    """
    for offer in portfolio.offerList:
        if offer.status in (None, models.OfferStatus.EMPTY) or offer.readyToCollect:
            continue
        if (
            (offer.status == models.OfferStatus.BUY and any(o.itemId == offer.itemId and o.slotIndex != offer.slotIndex for o in portfolio.offerList))
            or (offer.status == models.OfferStatus.BUY and offer.price != prices.get(offer.itemId, {}).get("bid"))
            or (offer.status == models.OfferStatus.BUY and pd.isna(prices.get(offer.itemId, {}).get("ask")))
            or (offer.status == models.OfferStatus.SELL and offer.price != prices.get(offer.itemId, {}).get("ask", offer.price))
            or (offer.status == models.OfferStatus.BUY and not active_offers_cache.is_oldest_offer(offer.itemId, user))
            or (offer.status == models.OfferStatus.BUY and tax.get_post_tax_price(offer.itemId, prices.get(offer.itemId, {}).get("ask")) - offer.price <= 0 and offer.itemId != osrs_constants.BOND_TRADEABLE_ID)
        ):
            return models.ActionData(action=models.ActionEnum.CANCEL, slotIndex=offer.slotIndex)
    return None

def check_collect(portfolio: models.Portfolio) -> models.ActionData | None:
    """
    Check for any offers ready to collect.

    Parameters
    ----------
    portfolio : models.Portfolio
        Instance's portfolio.

    Returns
    -------
    models.ActionData or None
        Action to collect completed offer, or None if no collection is needed.
    """
    for offer in portfolio.offerList:
        if offer.status in (None, models.OfferStatus.EMPTY) or not offer.readyToCollect: 
            continue
        return models.ActionData(action=models.ActionEnum.COLLECT, slotIndex=offer.slotIndex)
    return None

def check_ask(portfolio: models.Portfolio, prices: dict, askables: list[int], members_days_left: int) -> models.ActionData | None:
    """
    Decide whether to list any items for sale.

    Parameters
    ----------
    portfolio : models.Portfolio
        Instance's portfolio.
    prices : dict
        Current market prices.
    askables : list[int]
        List of item IDs that can be listed for sale.
    members_days_left : int
        Instance's number of membership days left.

    Returns
    -------
    models.ActionData or None
        Action to place a sell order, or None.
    """
    if not empty_slot_available(portfolio, members_days_left) or not askables: 
        return None
    for inv_item in portfolio.inventoryItemList:
        if inv_item.itemId not in askables or pd.isna(prices.get(inv_item.itemId, {}).get("ask")): 
            continue
        ideal = portfolio.inventoryItemList.count(inv_item.itemId)
        maximum = osrs_constants.MAX_CASH // prices[inv_item.itemId]["ask"]
        quantity = min(ideal, maximum)
        if quantity <= 0: 
            continue
        return models.ActionData(action=models.ActionEnum.ASK, itemId=inv_item.itemId, quantity=quantity, price=prices[inv_item.itemId]["ask"])
    return None

def check_bond(portfolio: models.Portfolio, prices: dict, members_days_left: int) -> models.ActionData | None:
    """
    Check whether a bond purchase or redemption is needed.

    Parameters
    ----------
    portfolio : models.Portfolio
        Instance's portfolio.
    prices : dict
        Market prices.
    members_days_left : int
        Instance's number of membership days left.

    Returns
    -------
    models.ActionData or None
        Action to redeem or buy a bond, or None.
    """
    if members_days_left > config.AUTO_BOND_DAYS: 
        return None
    if any(invItem.itemId in [osrs_constants.BOND_TRADEABLE_ID, osrs_constants.BOND_UNTRADEABLE_ID] for invItem in portfolio.inventoryItemList): 
        return models.ActionData(action=models.ActionEnum.BOND)
    if (
        empty_slot_available(portfolio, members_days_left)
        and not pd.isna(prices.get(osrs_constants.BOND_TRADEABLE_ID, {}).get("bid"))
        and portfolio.inventoryItemList.get_cash() >= prices[osrs_constants.BOND_TRADEABLE_ID]["bid"]
        and not portfolio.offerList.contains(osrs_constants.BOND_TRADEABLE_ID)
    ):
        return models.ActionData(action=models.ActionEnum.BID, itemId=osrs_constants.BOND_TRADEABLE_ID, quantity=1, price=prices[osrs_constants.BOND_TRADEABLE_ID]["bid"])
    return None

def check_bid(portfolio: models.Portfolio, prices: dict, order: list[int], biddables: list[int], members_days_left: int, user: str) -> models.ActionData | None:
    """
    Decide whether to place a buy offer for any item.

    Parameters
    ----------
    portfolio : models.Portfolio
        Instance's portfolio.
    prices : dict
        Market prices.
    order : list[int]
        Ranked item IDs by profitability.
    biddables : list[int]
        Items eligible to be bought.
    members_days_left : int
        Instance's number membership days of.
    user : str
        Instance's identifier (username).

    Returns
    -------
    models.ActionData or None
        Action to place a bid, or None.
    """
    if not empty_slot_available(portfolio, members_days_left) or not biddables:
        return None
    mapping = wiki_cache.get_mapping()["data"]
    limits = four_hour_limits.FourHourLimits(user)
    cash = portfolio.inventoryItemList.get_cash()
    for item_id in order:
        if item_id not in biddables or pd.isna(prices.get(item_id, {}).get("bid")) or pd.isna(prices.get(item_id, {}).get("ask")):
            continue
        bid = prices[item_id]["bid"]
        ask = prices[item_id]["ask"]
        if tax.get_post_tax_price(item_id, ask) - bid <= 0:
            continue
        potential = limits.get_remaining(item_id, mapping[item_id].get('limit', float('inf')))
        affordable = math.ceil(0.8 * cash) // bid
        quantity = min(potential, affordable)
        if quantity <= 0: 
            continue
        return models.ActionData(action=models.ActionEnum.BID, itemId=item_id, quantity=quantity, price=bid)
    return None

def get_biddables(user: str, members_days_left: int, trade_restricted: bool) -> list[int]:
    """
    Return list of items eligible for buying.

    Parameters
    ----------
    user : str
        Instance's identifier (username); filters active offers and four-hour limits.
    members_days_left : int
        Instance's number of membership days left; filters member-only items.
    trade_restricted : bool
        Instance's trade restricted status; filters trade-restricted items.

    Returns
    -------
    list[int]
        Item IDs eligible to be bought.
    """
    mapping = wiki_cache.get_mapping()["data"]
    limits = four_hour_limits.FourHourLimits(user)
    return [
        item_id for item_id in mapping.keys() if (
            (members_days_left > 0 or not mapping[item_id]['members'])
            and (not trade_restricted or item_id not in osrs_constants.TRADE_RESTRICTED_IDS)
            and (limits.get_remaining(item_id, mapping[item_id].get('limit', float('inf'))) > 0)
            and (not active_offers_cache.contains(item_id))
            and (item_id != osrs_constants.BOND_TRADEABLE_ID)
        )
    ]

def get_askables(portfolio: models.Portfolio, members_days_left: int, trade_restricted: bool) -> list[int]:
    """
    Return list of items eligible for selling.

    Parameters
    ----------
    portfolio : models.Portfolio
        Instance's portfolio; filters active offers and items in inventory.
    members_days_left : int
        Instance's number of membership days left; filters member-only items.
    trade_restricted : bool
        Instance's trade restricted status; filters trade-restricted items.

    Returns
    -------
    list[int]
        Item IDs in inventory that are valid to sell.
    """
    mapping = wiki_cache.get_mapping()["data"]
    return [
        item_id for item_id in mapping.keys() if (
            (item_id in [inv.itemId for inv in portfolio.inventoryItemList])
            and (item_id not in [offer.itemId for offer in portfolio.offerList])
            and (not trade_restricted or item_id not in osrs_constants.TRADE_RESTRICTED_IDS)
            and (item_id != osrs_constants.BOND_TRADEABLE_ID)
        )
    ]

def empty_slot_available(portfolio: models.Portfolio, members_days_left: int) -> bool:
    """
    Check if there is at least one empty GE offer slot.

    Parameters
    ----------
    portfolio : models.Portfolio
        Instance's portfolio.
    members_days_left : int
        Instance's number of membership days left.

    Returns
    -------
    bool
        True if there is at least one empty slot available, False otherwise.
    """
    slots = osrs_constants.P2P_OFFER_SLOTS if members_days_left > 0 else osrs_constants.F2P_OFFER_SLOTS
    for offer in portfolio.offerList:
        if (offer.status in (None, models.OfferStatus.EMPTY)) and offer.slotIndex in slots:
            return True
    return False