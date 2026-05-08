from __future__ import annotations

from pydantic import BaseModel


class ContactOut(BaseModel):
    id: int
    wa_id: str
    name: str | None
    is_group: bool
    allowed: bool


class ContactPatch(BaseModel):
    allowed: bool | None = None
    name: str | None = None
