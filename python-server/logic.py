
import re
import os
import json
import time

import active_offers_cache
import prices_cache
import osrs_constants
import config

# ------------------------------
# Next Action Logic
# ------------------------------

def getActionData(data):
    # data follows this structure:
    # data.get("portfolio", {}).get("offerList", [])
    # data.get("portfolio", {}).get("tradeList", [])
    # data.get("user", "")
    # data.get("membersDaysLeft", 14)
    # data.get("tradeRestricted", True)

    update_active_offers(data)

    biddables = get_biddables(data)
    askables = get_askables(data)
    _, order = get_prices_and_order('1h', T=12)
    prices, _ = get_prices_and_order('5m', T=12)

    actionData = check_cancel(data, prices)
    if actionData: return actionData
    actionData = check_collect(data)
    if actionData: return actionData
    actionData = check_ask(data, prices, askables)
    if actionData: return actionData
    actionData = check_bond(data, prices)
    if actionData: return actionData
    actionData = check_bid(data, prices, order, biddables)
    if actionData: return actionData
    return {"action": "IDLE", "itemId": None, "quantity": None, "price": None, "slotIndex": None, "text": None}

def update_active_offers(data):
    active_offers_cache.clear_stale()
    user = data.get("user")
    active_ids = {
        offer["itemId"]
        for offer in data.get("portfolio", {}).get("offerList", [])
        if offer.get("status", "EMPTY") != "EMPTY"
    }
    active_offers_cache.sync_user(user, active_ids)

def check_cancel(data, prices):
    for offer in data.get("portfolio", {}).get("offerList", []):
        if offer.get("status", "EMPTY") == "EMPTY" or offer["readyToCollect"]: continue
        if (
            (offer["status"] == "BUY" and offer["price"] != prices.get(offer["itemId"], {}).get("bid", 0)) # price mismatch
            or
            (offer["status"] == "SELL" and offer["price"] != prices.get(offer["itemId"], {}).get("ask", offer["price"])) # price mismatch
            or 
            (offer["status"] == "BUY" and not active_offers_cache.is_oldest_offer(offer["itemId"], data["user"])) # someone else offered it first - so we don't end up with 10 bots all bidding Death Rune the instant prices update
            or
            (offer["status"] == "BUY" and get_post_tax_price(offer["itemId"], prices.get(offer["itemId"], {}).get("ask", 0)) - offer["price"] <= 0 and offer["itemId"] != osrs_constants.BOND_TRADEABLE_ID) # buying an item that is no longer profitable
        ):
            return {"action": "CANCEL", "itemId": None, "quantity": None, "price": None, "slotIndex": offer["slotIndex"], "text": None}
    return None

def check_collect(data):
    offer_list = data.get("portfolio", {}).get("offerList", [])
    for offer in offer_list:
        if offer.get("status", "EMPTY") == "EMPTY" or not offer["readyToCollect"]: continue
        return {"action": "COLLECT", "itemId": None, "quantity": None, "price": None, "slotIndex": offer["slotIndex"], "text": None}
    return None 

def check_ask(data, prices, askables):
    if not empty_slot_available(data) or not askables: return None
    for inv_item in data['portfolio']['inventoryItemList']:
        if inv_item["itemId"] not in askables or prices.get(inv_item["itemId"],{}).get("ask", None) is None: continue
        return {"action": "ASK", "itemId": inv_item["itemId"], "quantity": count(data, inv_item['itemId']), "price": prices[inv_item["itemId"]]["ask"], "slotIndex": None, "text": None}
    return None 

def check_bond(data, prices):
    if data["membersDaysLeft"] > config.AUTO_BOND_DAYS: return None
    if (
        osrs_constants.BOND_TRADEABLE_ID in [inv_item["itemId"] for inv_item in data['portfolio']['inventoryItemList']]
        or
        osrs_constants.BOND_UNTRADEABLE_ID in [inv_item["itemId"] for inv_item in data['portfolio']['inventoryItemList']]
    ): 
        return {"action": "BOND", "itemId": None, "quantity": None, "price": None, "slotIndex": None, "text": None}
    if (
        empty_slot_available(data)
        and
        prices.get(osrs_constants.BOND_UNTRADEABLE_ID, {}).get("bid", None) is not None
        and
        get_cash(data) >= prices[osrs_constants.BOND_TRADEABLE_ID]["bid"]
    ):
        return {"action": "BOND", "itemId": osrs_constants.BOND_TRADEABLE_ID, "quantity": 1, "price": prices[osrs_constants.BOND_TRADEABLE_ID]["bid"], "slotIndex": None, "text": None}
    return None 

def check_bid(data, prices, order, biddables):
    if not empty_slot_available(data) or not biddables: return None
    mapping = prices_cache.get_mapping_data()
    four_hour_limits = load_four_hour_limits(data['user'])
    cash = get_cash(data)
    for item_id in order:
        if item_id not in biddables or prices.get(item_id, {}).get("bid", None) is None or prices.get(item_id, {}).get("ask", None) is None: continue
        bid, ask = prices[item_id]["bid"], prices[item_id]["ask"]
        if get_post_tax_price(item_id, ask) - bid <= 0: continue
        potential = remaining_four_hour_limit(four_hour_limits.get(item_id, {"lastReset": 0, "usedLimit": 0}), mapping[item_id].get('limit', float('inf')))
        affordable = cash // bid
        quantity = min(potential, affordable)
        if quantity <= 0: continue
        return {"action": "BID", "itemId": item_id, "quantity": quantity, "price": bid, "slotIndex": None, "text": None}
    return None 

def get_biddables(data):
    mapping = prices_cache.get_mapping_data()
    four_hour_limits = load_four_hour_limits(data['user'])
    items = [item_id for item_id in mapping]
    items = [item_id for item_id in items if data['membersDaysLeft'] > 0 or not mapping[item_id]['members']]
    items = [item_id for item_id in items if not data['tradeRestricted'] or not item_id in osrs_constants.TRADE_RESTRICTED_IDS]
    items = [item_id for item_id in items if remaining_four_hour_limit(four_hour_limits.get(item_id, {"lastReset": 0, "usedLimit": 0}), mapping[item_id].get('limit', float('inf'))) > 0]
    items = [item_id for item_id in items if not active_offers_cache.contains(item_id)]
    items = [item_id for item_id in items if item_id != osrs_constants.BOND_TRADEABLE_ID]
    return items

def get_askables(data):
    mapping = prices_cache.get_mapping_data()
    items = [item_id for item_id in mapping]
    items = [item_id for item_id in items if item_id in [inv_item['itemId'] for inv_item in data['portfolio']['inventoryItemList']]]
    items = [item_id for item_id in items if item_id not in [offer['itemId'] for offer in data['portfolio']['offerList']]]
    items = [item_id for item_id in items if not data['tradeRestricted'] or not item_id in osrs_constants.TRADE_RESTRICTED_IDS]
    items = [item_id for item_id in items if item_id != osrs_constants.BOND_TRADEABLE_ID]
    return items

# Simple algo: bid is avg low price, ask is avg high price, order is by profit: (ask - bid) * volume
def get_prices_and_order(series='5m', T=12, ids=None):
    fetch_fn = {
        '5m': prices_cache.get_5m_data,
        '1h': prices_cache.get_1h_data
    }.get(series)
    if fetch_fn is None:
        raise ValueError(f"Unsupported series: {series}")

    raw = {}
    for i in reversed(range(1, T + 1)):
        for k, v in fetch_fn(t=-i).items():
            if ids is not None and k not in ids:
                continue
            raw.setdefault(k, []).append(v)

    prices = {}
    for k, records in raw.items():
        bid_sum = ask_sum = vol_sum = 0.0
        bid_count = ask_count = 0

        for r in records:
            avg_low = r.get("avgLowPrice")
            avg_high = r.get("avgHighPrice")
            low_vol = r.get("lowPriceVolume") or 0
            high_vol = r.get("highPriceVolume") or 0

            if avg_low is not None:
                bid_sum += avg_low
                bid_count += 1
            if avg_high is not None:
                ask_sum += avg_high
                ask_count += 1

            vol_sum += low_vol + high_vol

        if bid_count > 0 and ask_count > 0:
            bid = int(bid_sum / bid_count)
            ask = int(ask_sum / ask_count)
            prices[k] = {
                "bid": bid,
                "ask": ask,
                "pre_tax_margin": ask - bid,
                "profit": (get_post_tax_price(k, ask) - bid) * vol_sum
            }

    order = sorted(prices, key=lambda k: (prices[k]['pre_tax_margin'] < 2, -prices[k]['profit'])) # to avoid items like Air Rune, Fire Rune, Feather, etc... and sort by profit

    return prices, order

# ------------------------------
# Porftolio Helpers
# ------------------------------

def empty_slot_available(data):
    slots = osrs_constants.P2P_OFFER_SLOTS if data["membersDaysLeft"] > 0 else osrs_constants.F2P_OFFER_SLOTS
    for offer in data.get("portfolio", {}).get("offerList", []):
        if offer.get("status", "EMPTY") == "EMPTY" and offer.get("slotIndex", -1) in slots: 
            return True
    return False

def get_cash(data):
    cash = 0
    for inv_item in data.get("portfolio", {}).get("inventoryItemList", []):
        if inv_item.get("itemId") == osrs_constants.COINS_ID:
            cash += inv_item.get("quantity", 0)
    return cash

def count(data, item_id):
    count = 0
    for inv_item in data.get("portfolio", {}).get("inventoryItemList", []):
        if inv_item.get("itemId") == item_id:
            count += inv_item.get("quantity", 0)
    return count

# ------------------------------
# Utils
# ------------------------------

def get_post_tax_price(item_id, price):
    if item_id in osrs_constants.TAX_EXEMPT_IDS: return price
    return max(price - int(osrs_constants.GE_TAX_RATE * price), price - osrs_constants.MAX_GE_TAX) 

# ------------------------------
# Four Hour Limits Logic
# ------------------------------

def update_four_limits(data):
    newTradeList = data.get("tradeList")
    user = data.get("user")
    four_hour_limits = load_four_hour_limits(user)
    for trade in newTradeList:
        if not trade or trade['quantity'] <= 0: continue
        four_hour_limit = four_hour_limits.get(trade["itemId"], {"lastReset": 0, "usedLimit": 0})
        four_hour_limit = update_four_limit(four_hour_limit, trade)
        four_hour_limits[trade["itemId"]] = four_hour_limit
    save_four_hour_limits_json(user, four_hour_limits)

def update_four_limit(four_hour_limit, trade):
    if is_over_four_hours_ago(four_hour_limit["lastReset"]): four_hour_limit["usedLimit"] = 0
    if four_hour_limit["usedLimit"] == 0: four_hour_limit["lastReset"] = trade["timestamp"]
    four_hour_limit["usedLimit"] += trade["quantity"]
    return four_hour_limit    

def remaining_four_hour_limit(four_hour_limit, limit):
    if is_over_four_hours_ago(four_hour_limit["lastReset"]): four_hour_limit["usedLimit"] = 0
    return max(0, limit - four_hour_limit["usedLimit"])

def is_over_four_hours_ago(unix_ts):
    return time.time() - unix_ts > 4 * 60 * 60

def load_four_hour_limits(user):
    file_path = get_four_hour_limits_path(user)
    if not os.path.exists(file_path): return {}
    with open(file_path, 'r') as file: return {int(k): v for k, v in json.load(file).items()}

def save_four_hour_limits_json(user, four_hour_limits):
    file_path = get_four_hour_limits_path(user)
    with open(file_path, 'w') as file: json.dump(four_hour_limits, file, indent=4)

def get_four_hour_limits_path(user):
    path = config.DATA_DIR / "fourHourLimits" / f"{sanitise_filename(user)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)

def sanitise_filename(string):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", string).strip().rstrip(". ")