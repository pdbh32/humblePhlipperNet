from dataclasses import dataclass

@dataclass(frozen=True)
class Quote:
    item_id: int | None = None
    bid_price: int | None = None
    ask_price: int | None = None
    bid_quantity: int | None = None
    ask_quantity: int | None = None
