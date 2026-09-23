from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

from app.models import Priority, Status

TitleStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)
]
DescriptionStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
TagStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
]


class TicketBase(BaseModel):
    title: TitleStr
    description: DescriptionStr
    priority: Priority = Priority.MEDIUM
    tags: list[TagStr] = Field(default_factory=list, max_length=20)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, tags: list[str]) -> list[str]:
        # Lowercase + dedupe so tag filters stay predictable.
        return list(dict.fromkeys(tag.lower() for tag in tags))


class TicketCreate(TicketBase):
    model_config = ConfigDict(extra="forbid")

    # Status is intentionally absent: every ticket starts OPEN, and extra="forbid"
    # rejects a caller that tries to set it rather than silently dropping it.
    assigned_to: EmailStr | None = None


class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: Status
    assigned_to: EmailStr | None = None
    created_at: datetime
    updated_at: datetime


class TicketClaim(BaseModel):
    assigned_to: EmailStr


class TicketStatusUpdate(BaseModel):
    status: Status
