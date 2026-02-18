from __future__ import annotations

from humblePhlipperPython.config.runtime import SESSION_TIMESTAMP
from humblePhlipperPython.schemata.api.report_events_request import ReportEventsRequest
from humblePhlipperPython.schemata.domain.four_hour_limit import FourHourLimit
from humblePhlipperPython.schemata.domain.event import Label as EventLabel
from humblePhlipperPython.caches import four_hour_limits as four_hour_limits_cache
from humblePhlipperPython.storage import four_hour_limits as four_hour_limits_storage
from humblePhlipperPython.storage import events as events_storage

def ingest_reported_events(rer: ReportEventsRequest) -> None:
    limits = four_hour_limits_cache.get(rer.user)
    if not limits: limits = four_hour_limits_storage.load(rer.user)
    for event in rer.event_list:
        if event is None or event.label != EventLabel.TRADE:
            continue
        limits.setdefault(event.item_id, FourHourLimit()).update(event)
    four_hour_limits_cache.set(rer.user, limits)
    four_hour_limits_storage.save(rer.user, limits)
    events_storage.save(rer.user, SESSION_TIMESTAMP, rer.event_list)