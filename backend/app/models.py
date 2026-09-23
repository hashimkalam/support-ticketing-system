import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, String, Text, func, text
# Postgres ARRAY (not the generic one) so tags support contains()/overlap().
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Status(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class Ticket(Base):
    __tablename__ = "tickets"

    # UUIDs keep ticket IDs non-guessable in the public API.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # VARCHAR + CHECK instead of a native PG enum: new priorities are a
    # constraint swap rather than an ALTER TYPE migration.
    priority: Mapped[Priority] = mapped_column(
        Enum(
            Priority,
            name="ticket_priority",
            native_enum=False,
            length=20,
            # Persist .value ("high"), not the member name, so the CHECK
            # constraint matches the column default and API payloads.
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=Priority.MEDIUM,
        server_default=Priority.MEDIUM.value,
        index=True,
    )

    status: Mapped[Status] = mapped_column(
        Enum(
            Status,
            name="ticket_status",
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=Status.OPEN,
        server_default=Status.OPEN.value,
        index=True,
    )

    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        default=list,
        server_default=text("'{}'::varchar[]"),
    )

    # Nullable until an agent claims the ticket.
    assigned_to: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        # GIN keeps tag containment filters (`tags @> ARRAY[...]`) index-backed.
        Index("ix_tickets_tags_gin", "tags", postgresql_using="gin"),
        # Status and assignment cannot drift: only OPEN may be unassigned.
        CheckConstraint(
            "status = 'open' OR assigned_to IS NOT NULL",
            name="ck_tickets_status_requires_assignee",
        ),
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} status={self.status} priority={self.priority}>"
