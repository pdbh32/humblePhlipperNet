import time

from pydantic import BaseModel

from humblePhlipperPython.schemata.domain.event import Event, Label as EventLabel

FOUR_HOURS_IN_SECONDS = 4 * 60 * 60

class FourHourLimit(BaseModel):
    last_reset: int = 0
    used_limit: int = 0

    def update(self, trade: Event) -> None:
        if not trade or trade.label != EventLabel.TRADE or trade.quantity <= 0: # if not a buy
            return
        if time.time() - self.last_reset > FOUR_HOURS_IN_SECONDS:
            self.used_limit = 0
        if self.used_limit == 0:
            self.last_reset = trade.timestamp
        self.used_limit += trade.quantity

    def remaining(self, limit: int) -> int:
        if time.time() - self.last_reset > FOUR_HOURS_IN_SECONDS:
            self.used_limit = 0
        return max(0, limit - self.used_limit)