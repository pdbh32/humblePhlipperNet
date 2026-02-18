from __future__ import annotations

from humblePhlipperPython.config.runtime import SESSION_TIMESTAMP
from humblePhlipperPython.schemata.api.next_command_request import NextCommandRequest
from humblePhlipperPython.schemata.domain.event import Label as EventLabel
from humblePhlipperPython.schemata.domain.offer import Offer, Status as OfferStatus
from humblePhlipperPython.caches import four_hour_limits as four_hour_limits_cache, command_requests as command_requests_cache, quotes as quotes_cache, market_data as market_data_cache
from humblePhlipperPython.storage import four_hour_limits as four_hour_limits_storage, events as events_storage
from humblePhlipperPython.core import logic

def build_next_command(ncr: NextCommandRequest):
    # update caches
    command_requests_cache.set(ncr.user, ncr)
    limits = four_hour_limits_cache.get(ncr.user)
    if not limits: 
        limits = four_hour_limits_storage.load(ncr.user)
        four_hour_limits_cache.set(ncr.user, limits)
    command_requests_cache.set(ncr.user, ncr)

    # generate command
    command_event = logic.select_next_command(
        my_offers=ncr.offer_list,                   
        my_inventory=ncr.inventory_item_list, 
        user=ncr.user,                                 
        members_days_left=ncr.members_days_left,                   
        trade_restricted=ncr.trade_restricted,                    
        limits=limits,         
        others_offers={user: request.offer_list for user, request in command_requests_cache.get().items() if user != ncr.user},
        others_inventories={user: request.inventory_item_list for user, request in command_requests_cache.get().items() if user != ncr.user},     
        base_quotes=quotes_cache.get(),           
        mappings=market_data_cache.get_latest("mapping")["data"]         
    )

    # update caches
    if command_event.label != EventLabel.IDLE: 
        events_storage.save(ncr.user, SESSION_TIMESTAMP, [command_event])
    if command_event.label in [EventLabel.BID, EventLabel.ASK]:
        offer_list = [*ncr.offer_list, Offer(status=OfferStatus.BUY if command_event.label == EventLabel.BID else OfferStatus.SELL, item_id=command_event.item_id)]
        command_requests_cache.set(ncr.user, ncr.model_copy(update={"offer_list": offer_list})) # stop-gap: spoof a quote to stop other users bidding the item before the cache updates properly
    
    return command_event        