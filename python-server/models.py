from __future__ import annotations
from enum import Enum
from typing import List, Optional, Iterator
from pydantic import BaseModel, Field
from collections import defaultdict
from io import StringIO
import csv

import tax 
import osrs_constants

class ActionEnum(str, Enum):
    BID = "BID"
    ASK = "ASK"
    CANCEL = "CANCEL"
    COLLECT = "COLLECT"
    BOND = "BOND"
    IDLE = "IDLE"
    ERROR = "ERROR"

class ActionData(BaseModel):
    action: ActionEnum
    itemId: Optional[int] = None
    quantity: Optional[int] = None
    price: Optional[int] = None
    slotIndex: Optional[int] = None
    text: Optional[str] = None

class InventoryItem(BaseModel):
    itemId: int
    quantity: int

class InventoryItemList(BaseModel):
    __root__: List[InventoryItem]

    def __iter__(self):
        return iter(self.__root__)

    def get_item_id_set(self) -> set[int]:
        return {item.itemId for item in self.__root__}

    def count(self, item_id: int) -> int:
        return sum(item.quantity for item in self.__root__ if item.itemId == item_id)

    def get_cash(self) -> int:
        return sum(item.quantity for item in self.__root__ if item.itemId == osrs_constants.COINS_ID)

class OfferStatus(str, Enum):
    EMPTY = "EMPTY"
    BUY = "BUY"
    SELL = "SELL"

class Offer(BaseModel):
    slotIndex: int = Field(-1)
    itemId: int = -1
    itemName: Optional[str] = None
    vol: int = 0
    price: int = 0
    transferredVol: int = 0
    transferredValue: int = 0
    readyToCollect: bool = False
    status: Optional[OfferStatus] = None

    def is_ready_to_collect(self) -> bool:
        return self.readyToCollect

class OfferList(BaseModel):
    __root__: List[Offer]

    def __iter__(self):
        return iter(self.__root__)

    def get_item_id_set(self) -> set[int]:
        return {offer.itemId for offer in self.__root__}

    def contains(self, item_id: int) -> bool:
        return any(offer.itemId == item_id for offer in self.__root__)

    def get_by_item_id(self, item_id: int) -> Optional[Offer]:
        for offer in self.__root__:
            if offer.itemId == item_id:
                return offer
        return None

    def get_buy_offer_values(self):
        return sum(offer.price * offer.vol for offer in self.__root__ if offer.status == OfferStatus.BUY)

class Trade(BaseModel):
    timestamp: int
    itemId: int
    itemName: str
    quantity: int
    price: float

class TradeList(BaseModel):
    __root__: List[Trade]

    def __init__(self, trades: Optional[List[Trade]] = None):
        super().__init__(__root__=trades or [])

    def __iter__(self) -> Iterator[Trade]:
        return iter(self.__root__)

    def __getitem__(self, index: int) -> Trade:
        return self.__root__[index] 

    def __len__(self) -> int:
        return len(self.__root__)    

    def increment(self, trade: Trade) -> None:
        self.__root__.append(trade)

    def split_by_name(self) -> dict[str, TradeList]:
        by_name: dict[str, TradeList] = {}
        for trade in self.__root__:
            if trade.itemName not in by_name:
                by_name[trade.itemName] = TradeList()
            by_name[trade.itemName].increment(trade)
        return by_name

    @staticmethod
    def _get_item_sublist_profit(trade_list: TradeList) -> float:
        trades = trade_list.__root__
        avg_buy_price = None
        avg_sell_price = None
        inventory = 0.0
        profit = 0.0

        for trade in trades:
            if trade.quantity > 0:
                if inventory < 0 and avg_sell_price is not None:
                    profit += (tax.get_post_tax_price(trade.itemId, avg_sell_price) - trade.price) * min(trade.quantity, abs(inventory))
                avg_buy_price = trade.price if avg_buy_price is None else (trade.quantity * trade.price + inventory * avg_buy_price) / (trade.quantity + inventory) # trade.quantity is > 0, if avg_buy_price is not None inventory must be > 0
            elif trade.quantity < 0:
                if inventory > 0 and avg_buy_price is not None:
                    profit += (tax.get_post_tax_price(trade.itemId, trade.price) - avg_buy_price) * min(-trade.quantity, inventory)
                avg_sell_price = trade.price if avg_sell_price is None else (trade.quantity * trade.price + inventory * avg_sell_price) / (trade.quantity + inventory) # trade.quantity is < 0, if avg_sell_price is not None inventory must be < 0

            inventory += trade.quantity
            if inventory <= 0:
                avg_buy_price = None
            if inventory >= 0:
                avg_sell_price = None

        return profit

    def get_item_name_profit_map(self) -> dict[str, float]:
        return {name: self._get_item_sublist_profit(trade_list) for name, trade_list in self.split_by_name().items()}

    def get_sorted_item_name_profit_list(self) -> list[tuple[str, float]]:
        return sorted(self.get_item_name_profit_map().items(), key=lambda x: (-x[1], x[0]))

    def get_total_profit(self) -> int:
        return int(sum(self.get_item_name_profit_map().values()))


class Portfolio(BaseModel):
    offerList: OfferList = Field(default_factory=lambda: OfferList(__root__=[]))
    inventoryItemList: InventoryItemList = Field(default_factory=lambda: InventoryItemList(__root__=[]))

    def get_liquid_value(self) -> int:
        return self.inventoryItemList.get_cash() + self.offerList.get_buy_offer_values()
    
class ActionRequest(BaseModel):
    portfolio: Portfolio
    user: str
    membersDaysLeft: int = -1
    tradeRestricted: bool = True
