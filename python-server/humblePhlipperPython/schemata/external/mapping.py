from pydantic import BaseModel

class Mapping(BaseModel):
    examine: str
    id: int
    members: bool
    lowalch: int | None = None  # not always present in https://prices.runescape.wiki/api/v1/osrs/mapping
    limit: int | None = None    # not always present in https://prices.runescape.wiki/api/v1/osrs/mapping
    value: int | None = None    # not always present in https://prices.runescape.wiki/api/v1/osrs/mapping
    highalch: int | None = None # not always present in https://prices.runescape.wiki/api/v1/osrs/mapping
    icon: str
    name: str
