import re
import time
import json
import os

import config
import models

FOUR_HOURS_IN_SECONDS = 4 * 60 * 60


def sanitise_filename(string):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", string).strip().rstrip(".")


class FourHourLimit:
    def __init__(self, last_reset: float = 0, used_limit: int = 0):
        self.last_reset = last_reset
        self.used_limit = used_limit

    @classmethod
    def from_dict(cls, d):
        return cls(
            last_reset=d.get("lastReset", 0),
            used_limit=d.get("usedLimit", 0)
        )

    def to_dict(self):
        return {
            "lastReset": self.last_reset,
            "usedLimit": self.used_limit
        }

    def update(self, trade):
        if time.time() - self.last_reset > FOUR_HOURS_IN_SECONDS:
            self.used_limit = 0
        if self.used_limit == 0:
            self.last_reset = trade["timestamp"]
        self.used_limit += trade["quantity"]

    def remaining(self, limit):
        if time.time() - self.last_reset > FOUR_HOURS_IN_SECONDS:
            self.used_limit = 0
        return max(0, limit - self.used_limit)


class FourHourLimits:
    def __init__(self, user: str):
        self.user = user
        self.limits = self._load()

    def _get_path(self):
        path = config.DATA_DIR / "data" / "fourHourLimits" / f"{sanitise_filename(self.user)}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    def _load(self):
        path = self._get_path()
        if not os.path.exists(path):
            return {}
        with open(path, 'r') as f:
            raw = json.load(f)
            return {int(k): FourHourLimit.from_dict(v) for k, v in raw.items()}

    def save(self):
        with open(self._get_path(), 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.limits.items()}, f, indent=4)

    def update_with_trades(self, trades: models.TradeList):
        for trade in trades:
            if not trade or trade["quantity"] <= 0:
                continue
            limit = self.limits.get(trade["itemId"], FourHourLimit())
            limit.update(trade)
            self.limits[trade["itemId"]] = limit
        self.save()

    def get_remaining(self, item_id: int, limit_value: int) -> int:
        return self.limits.get(item_id, FourHourLimit()).remaining(limit_value)