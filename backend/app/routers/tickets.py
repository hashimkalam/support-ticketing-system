from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Status, Ticket
from app.schemas import TicketClaim, TicketCreate, TicketListResponse, TicketResponse

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=http_status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> Ticket:
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=TicketListResponse)
def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> TicketListResponse:
    total_count = db.scalar(select(func.count()).select_from(Ticket)) or 0

    # Explicit ordering: without it, offset paging may repeat or drop rows.
    stmt = (
        select(Ticket)
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return TicketListResponse(
        items=list(db.scalars(stmt).all()),
        total_count=total_count,
        skip=skip,
        limit=limit,
    )


@router.post("/{ticket_id}/claim", response_model=TicketResponse)
def claim_ticket(
    ticket_id: UUID, payload: TicketClaim, db: Session = Depends(get_db)
) -> Ticket:
    # Single conditional UPDATE: Postgres re-evaluates the predicate once the
    # competing row lock clears, so only one agent matches and the rest get 0 rows.
    stmt = (
        update(Ticket)
        .where(Ticket.id == ticket_id, Ticket.assigned_to.is_(None))
        .values(
            assigned_to=payload.assigned_to,
            status=Status.IN_PROGRESS,
            updated_at=func.now(),
        )
        .returning(Ticket)
        # Nothing in this session's identity map needs synchronizing.
        .execution_options(synchronize_session=False)
    )

    ticket = db.execute(stmt).scalar_one_or_none()
    if ticket is not None:
        db.commit()
        return ticket

    db.rollback()
    # Distinguish "already taken" from "never existed".
    existing = db.get(Ticket, ticket_id)
    if existing is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    # Re-claim by the current owner is a retry, not a conflict: return the row
    # untouched so a double-click never surfaces an error.
    if existing.assigned_to and existing.assigned_to.lower() == payload.assigned_to.lower():
        return existing

    raise HTTPException(
        status_code=http_status.HTTP_409_CONFLICT,
        detail=f"Ticket already assigned to {existing.assigned_to}",
    )
