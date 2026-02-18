from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

class Status(str, Enum):
    EMPTY = "EMPTY"
    BUY = "BUY"
    SELL = "SELL"

class Offer(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    item_id: int | None = Field(default=-1, alias="itemId")
    item_name: str | None = Field(default=None, alias="itemName")
    quantity: int | None = 0
    price: int | None = 0
    slot_index: int | None = Field(default=-1, alias="slotIndex")
    transferred_quantity: int | None = Field(default=0, alias="transferredQuantity")
    transferred_value: int | None = Field(default=0, alias="transferredValue")
    status: Status | None = None
    ready_to_collect: bool | None = Field(default=False, alias="readyToCollect")
