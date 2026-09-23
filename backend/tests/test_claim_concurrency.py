"""The claim guarantee is the point of this service, so it is tested under
real contention rather than asserted in prose.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import Status, Ticket

CLAIMANTS = 16


def _storm(
    client: TestClient, ticket_id: str, agents: list[str]
) -> list[tuple[int, dict]]:
    """Fire one claim per agent, all released from a shared barrier."""
    barrier = threading.Barrier(len(agents))
    lock = threading.Lock()
    outcomes: list[tuple[int, dict]] = []

    def claim(email: str) -> None:
        barrier.wait()
        response = client.post(
            f"/api/v1/tickets/{ticket_id}/claim", json={"assigned_to": email}
        )
        with lock:
            outcomes.append((response.status_code, response.json()))

    with ThreadPoolExecutor(max_workers=len(agents)) as pool:
        list(pool.map(claim, agents))

    return outcomes


def test_only_the_first_of_many_concurrent_claims_wins(
    client: TestClient, make_ticket, engine: Engine
) -> None:
    ticket_id = make_ticket()["id"]
    agents = [f"agent{index}@example.com" for index in range(CLAIMANTS)]

    outcomes = _storm(client, ticket_id, agents)

    winners = [body["assigned_to"] for status, body in outcomes if status == 200]
    conflicts = [body["detail"] for status, body in outcomes if status == 409]

    assert len(winners) == 1, f"expected exactly one winner, got {winners}"
    assert len(conflicts) == CLAIMANTS - 1
    # Every loser is told who won, rather than a bare "conflict".
    assert set(conflicts) == {f"Ticket already assigned to {winners[0]}"}

    with Session(engine) as session:
        stored = session.get(Ticket, ticket_id)
        assert stored.status == Status.IN_PROGRESS
        assert stored.assigned_to == winners[0]


def test_concurrent_retries_by_one_agent_all_succeed(
    client: TestClient, make_ticket, engine: Engine
) -> None:
    ticket_id = make_ticket()["id"]

    outcomes = _storm(client, ticket_id, ["alice@example.com"] * CLAIMANTS)

    assert {status for status, _ in outcomes} == {200}
    assert {body["assigned_to"] for _, body in outcomes} == {"alice@example.com"}

    with Session(engine) as session:
        stored = session.get(Ticket, ticket_id)
        assert stored.assigned_to == "alice@example.com"
        assert stored.status == Status.IN_PROGRESS
