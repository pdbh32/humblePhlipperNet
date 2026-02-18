from pydantic import BaseModel, ConfigDict, Field


class FiveMinute(BaseModel):  # not always present in https://prices.runescape.wiki/api/v1/osrs/5m
    model_config = ConfigDict(populate_by_name=True)

    avg_high_price: int | None = Field(default=None, alias="avgHighPrice")  # not always present
    high_price_volume: int | None = Field(default=0, alias="highPriceVolume")  # not always present
    avg_low_price: int | None = Field(default=None, alias="avgLowPrice")  # not always present
    low_price_volume: int | None = Field(default=0, alias="lowPriceVolume")  # not always present
