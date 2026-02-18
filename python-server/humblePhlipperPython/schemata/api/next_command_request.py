from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from humblePhlipperPython.schemata.domain.inventory_item import InventoryItem
from humblePhlipperPython.schemata.domain.offer import Offer


class NextCommandRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    offer_list: list[Offer | None] = Field(alias="offerList")
    inventory_item_list: list[InventoryItem] = Field(alias="inventoryItemList")
    user: str
    members_days_left: int = Field(alias="membersDaysLeft")
    trade_restricted: bool = Field(alias="tradeRestricted")

    @field_validator("offer_list", mode="before")
    @classmethod
    def _v_offer_list(cls, v: list[dict[str, Any] | None]) -> list[Offer | None]:
        return [Offer.model_validate(x) if x is not None else None for x in v]

    @field_validator("inventory_item_list", mode="before")
    @classmethod
    def _v_inventory_list(cls, v: list[dict[str, Any]]) -> list[InventoryItem]:
        return [InventoryItem.model_validate(x) for x in v]
