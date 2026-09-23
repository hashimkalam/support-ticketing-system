from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import Ticket


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/health/db").json() == {"status": "ok", "database": "reachable"}


def test_create_applies_documented_defaults(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tickets",
        json={"title": "Printer on fire", "description": "Sparks and smoke."},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "open"
    assert body["priority"] == "medium"
    assert body["assigned_to"] is None
    assert body["tags"] == []
    assert UUID(body["id"])
    assert body["created_at"] == body["updated_at"]


def test_create_normalises_tags(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tickets",
        json={
            "title": "Billing export",
            "description": "Totals are wrong.",
            "tags": ["Billing", "billing", "IT"],
        },
    )

    assert response.json()["tags"] == ["billing", "it"]


def test_create_rejects_client_supplied_status(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tickets",
        json={"title": "Sneaky", "description": "x", "status": "resolved"},
    )

    assert response.status_code == 422
    assert any(
        error["type"] == "extra_forbidden" for error in response.json()["detail"]
    )


def test_create_rejects_invalid_payloads(client: TestClient) -> None:
    cases = [
        {"title": "x", "description": "too short a title"},
        {"title": "Valid title", "description": ""},
        {"title": "Valid title", "description": "x", "priority": "critical"},
        {"title": "Valid title", "description": "x", "assigned_to": "not-an-email"},
    ]

    for payload in cases:
        assert client.post("/api/v1/tickets", json=payload).status_code == 422, payload


def test_get_ticket_by_id(client: TestClient, make_ticket) -> None:
    created = make_ticket(title="Fetch me")

    response = client.get(f"/api/v1/tickets/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_ticket_by_id_returns_404_for_unknown(client: TestClient) -> None:
    response = client.get("/api/v1/tickets/11111111-1111-1111-1111-111111111111")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}


def test_list_reports_total_and_paginates(client: TestClient, make_ticket) -> None:
    for index in range(3):
        make_ticket(title=f"Ticket {index}")

    page = client.get("/api/v1/tickets", params={"skip": 0, "limit": 2}).json()

    assert page["total_count"] == 3
    assert len(page["items"]) == 2
    assert page["skip"] == 0
    assert page["limit"] == 2

    last_page = client.get("/api/v1/tickets", params={"skip": 2, "limit": 2}).json()
    assert len(last_page["items"]) == 1


def test_list_orders_newest_first_and_pages_do_not_overlap(
    client: TestClient, engine: Engine
) -> None:
    base = datetime.now(timezone.utc)
    with Session(engine) as session:
        for index in range(5):
            session.add(
                Ticket(
                    title=f"Ticket {index}",
                    description="Seeded directly.",
                    created_at=base - timedelta(minutes=index),
                )
            )
        session.commit()

    first = client.get("/api/v1/tickets", params={"skip": 0, "limit": 3}).json()
    second = client.get("/api/v1/tickets", params={"skip": 3, "limit": 3}).json()

    assert [ticket["title"] for ticket in first["items"]] == [
        "Ticket 0",
        "Ticket 1",
        "Ticket 2",
    ]
    assert [ticket["title"] for ticket in second["items"]] == [
        "Ticket 3",
        "Ticket 4",
    ]

    # The bug this ordering exists to prevent: unstable sorting silently
    # repeating one row on page two while dropping another.
    first_ids = {ticket["id"] for ticket in first["items"]}
    second_ids = {ticket["id"] for ticket in second["items"]}
    assert not first_ids & second_ids


def test_list_rejects_out_of_range_paging(client: TestClient) -> None:
    for params in ({"limit": 101}, {"limit": 0}, {"skip": -1}):
        assert client.get("/api/v1/tickets", params=params).status_code == 422


def test_list_beyond_the_end_returns_an_empty_page(
    client: TestClient, make_ticket
) -> None:
    make_ticket()

    body = client.get("/api/v1/tickets", params={"skip": 500, "limit": 10}).json()

    assert body["items"] == []
    assert body["total_count"] == 1
