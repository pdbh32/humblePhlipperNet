from pydantic import BaseModel, ConfigDict, Field


class Latest(BaseModel):  # not always present in https://prices.runescape.wiki/api/v1/osrs/latest
    model_config = ConfigDict(populate_by_name=True)

    high: int | None = None
    high_time: int | None = Field(default=0, alias="highTime")
    low: int | None = None
    low_time: int | None = Field(default=0, alias="lowTime")
