from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from humblePhlipperPython.schemata.domain.event import Event

class ReportEventsRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    event_list: list[Event | None] = Field(alias="eventList")
    user: str

    @field_validator("event_list", mode="before")
    @classmethod
    def _v_event_list(cls, v: list[dict[str, Any] | None]) -> list[Event | None]:
        return [Event.model_validate(x) if x is not None else None for x in v]
