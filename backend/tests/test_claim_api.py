from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import Status, Ticket


def test_claim_assigns_and_starts_progress(client: TestClient, make_ticket) -> None:
    ticket = make_ticket()

    response = client.post(
        f"/api/v1/tickets/{ticket['id']}/claim",
        json={"assigned_to": "alice@example.com"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["assigned_to"] == "alice@example.com"
    assert body["status"] == "in_progress"
    assert body["updated_at"] > ticket["updated_at"]


def test_claim_by_second_agent_conflicts(client: TestClient, make_ticket) -> None:
    ticket = make_ticket()
    client.post(
        f"/api/v1/tickets/{ticket['id']}/claim",
        json={"assigned_to": "alice@example.com"},
    )

    response = client.post(
        f"/api/v1/tickets/{ticket['id']}/claim",
        json={"assigned_to": "bob@example.com"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Ticket already assigned to alice@example.com"}


def test_repeat_claim_by_the_same_agent_is_idempotent(
    client: TestClient, make_ticket, engine: Engine
) -> None:
    ticket = make_ticket()
    first = client.post(
        f"/api/v1/tickets/{ticket['id']}/claim",
        json={"assigned_to": "alice@example.com"},
    ).json()

    replay = client.post(
        f"/api/v1/tickets/{ticket['id']}/claim",
        json={"assigned_to": "alice@example.com"},
    )

    assert replay.status_code == 200
    assert replay.json()["assigned_to"] == "alice@example.com"
    # A retry is a no-op: the row must not be rewritten.
    assert replay.json()["updated_at"] == first["updated_at"]


def test_repeat_claim_matches_email_case_insensitively(
    client: TestClient, make_ticket
) -> None:
    ticket = make_ticket()
    client.post(
        f"/api/v1/tickets/{ticket['id']}/claim",
        json={"assigned_to": "alice@example.com"},
    )

    replay = client.post(
        f"/api/v1/tickets/{ticket['id']}/claim",
        json={"assigned_to": "Alice@Example.com"},
    )

    assert replay.status_code == 200


def test_claim_on_resolved_ticket_does_not_resurrect_it(
    client: TestClient, make_ticket, engine: Engine
) -> None:
    ticket = make_ticket()
    with Session(engine) as session:
        stored = session.get(Ticket, ticket["id"])
        stored.assigned_to = "alice@example.com"
        stored.status = Status.RESOLVED
        session.commit()

    replay = client.post(
        f"/api/v1/tickets/{ticket['id']}/claim",
        json={"assigned_to": "alice@example.com"},
    )

    assert replay.status_code == 200
    # The response body is the source of truth: a 200 does not imply in_progress.
    assert replay.json()["status"] == "resolved"


def test_claim_unknown_ticket_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/tickets/11111111-1111-1111-1111-111111111111/claim",
        json={"assigned_to": "alice@example.com"},
    )

    assert response.status_code == 404


def test_claim_rejects_malformed_input(client: TestClient, make_ticket) -> None:
    ticket = make_ticket()

    assert (
        client.post(
            "/api/v1/tickets/not-a-uuid/claim",
            json={"assigned_to": "alice@example.com"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/v1/tickets/{ticket['id']}/claim", json={"assigned_to": "nope"}
        ).status_code
        == 422
    )
