from pydantic import BaseModel, ConfigDict, Field

class InventoryItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    item_id: int = Field(alias="itemId")
    quantity: int
