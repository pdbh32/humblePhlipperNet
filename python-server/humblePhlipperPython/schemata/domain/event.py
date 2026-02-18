from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

class Label(str, Enum):
    START_POLLING = "START_POLLING"
    END_POLLING = "END_POLLING"
    TRADE = "TRADE"
    BID = "BID"
    ASK = "ASK"
    CANCEL = "CANCEL"
    COLLECT = "COLLECT"
    BOND = "BOND"
    IDLE = "IDLE"
    ERROR = "ERROR"

class Event(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    timestamp: int | None = None
    label: Label | None = None
    item_id: int | None = Field(default=None, alias="itemId")
    item_name: str | None = Field(default=None, alias="itemName")
    quantity: int | None = None
    price: int | None = None
    slot_index: int | None = Field(default=None, alias="slotIndex")
    text: str | None = None
