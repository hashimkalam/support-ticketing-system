"""Demo data so a fresh checkout has a populated queue to look at.

Runs only when SEED_DEMO_DATA is enabled, and only when the table is empty.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.database import SessionLocal, create_tables
from app.models import Priority, Status, Ticket

# Newest first; created_at is staggered below so pagination is demonstrable.
DEMO_TICKETS: list[dict] = [
    {
        "title": "Printer on fire",
        "description": "Sparks and smoke from the paper tray in the third-floor copy room. "
        "The floor has been evacuated and facilities are on the way.",
        "priority": Priority.URGENT,
        "tags": ["hardware", "facilities"],
    },
    {
        "title": "Laptop will not boot",
        "description": "Black screen straight after the latest OS update. Recovery mode "
        "loads, but the normal boot does not.",
        "priority": Priority.URGENT,
        "tags": ["hardware"],
    },
    {
        "title": "Wrong invoice total",
        "description": "The tax line appears twice on EU customer invoices, so the total "
        "is roughly 20% too high. Started after the billing release on Tuesday.",
        "priority": Priority.URGENT,
        "tags": ["billing"],
    },
    {
        "title": "VPN drops every 10 minutes",
        "description": "The tunnel resets on the corporate SSID but stays up on ethernet. "
        "Affecting about a dozen people in the Colombo office.",
        "priority": Priority.HIGH,
        "tags": ["network", "vpn"],
    },
    {
        "title": "Payroll export fails",
        "description": "The CSV export throws a 500 on the final step. Payroll run is due "
        "at the end of the week.",
        "priority": Priority.HIGH,
        "tags": ["billing", "payroll"],
    },
    {
        "title": "Slow dashboard queries",
        "description": "Analytics dashboards take over a minute to load during peak hours, "
        "which makes the morning standup unusable.",
        "priority": Priority.HIGH,
        "tags": ["performance"],
    },
    {
        "title": "Add SSO for contractors",
        "description": "Contractors currently share credentials for the internal tools. "
        "Security would like them on the same SSO tenant as staff.",
        "priority": Priority.MEDIUM,
        "tags": ["access", "security"],
    },
    {
        "title": "Password reset email never arrives",
        "description": "Tried three times, and there is nothing in the spam folder either. "
        "Confirmed the address is correct in the directory.",
        "priority": Priority.MEDIUM,
        "tags": ["access"],
    },
    {
        "title": "Slack notifications not firing",
        "description": "No alerts have reached the #incidents channel since the weekend, "
        "though the integration reports as healthy.",
        "priority": Priority.MEDIUM,
        "tags": ["integrations"],
    },
    {
        "title": "Onboarding doc out of date",
        "description": "The setup steps still reference the retired staging environment, "
        "so new joiners hit a dead end on day one.",
        "priority": Priority.MEDIUM,
        "tags": ["docs"],
    },
    {
        "title": "Request second monitor",
        "description": "Need a second display for the analytics dashboards during on-call "
        "shifts.",
        "priority": Priority.LOW,
        "tags": ["hardware"],
    },
    {
        "title": "Meeting room display blank",
        "description": "The HDMI switch powers on but reports no signal from any source. "
        "Happens in the large meeting room only.",
        "priority": Priority.LOW,
        "tags": ["facilities"],
    },
    {
        "title": "Email signature update",
        "description": "The company address changed last month; signatures still show the "
        "old office.",
        "priority": Priority.LOW,
        "tags": ["access"],
    },
    {
        "title": "Database failover drill",
        "description": "Scheduled failover exercise for the on-call rotation. Needs an owner "
        "from the platform team.",
        "priority": Priority.HIGH,
        "tags": ["infra"],
        "status": Status.IN_PROGRESS,
        "assigned_to": "priya@example.com",
    },
    {
        "title": "Migrate staging TLS certificate",
        "description": "Completed ahead of the expiry date. Certificate rotation is now "
        "scripted and documented in the runbook.",
        "priority": Priority.HIGH,
        "tags": ["infra", "security"],
        "status": Status.RESOLVED,
        "assigned_to": "arun@example.com",
    },
    {
        "title": "Q3 tax report reconciliation",
        "description": "Historical ticket kept for the billing audit trail. Totals were "
        "reconciled against the ledger and signed off by finance.",
        "priority": Priority.MEDIUM,
        "tags": ["billing", "reporting"],
        "status": Status.RESOLVED,
        "assigned_to": "nadia@example.com",
    },
]


def seed_demo_tickets() -> int:
    """Insert the demo set once. Returns how many rows were inserted."""
    with SessionLocal() as session:
        existing = session.scalar(select(func.count()).select_from(Ticket))
        if existing:
            return 0

        # Backdated so the newest demo ticket still looks freshly filed, while
        # created_at stays strictly before the database's own now() default.
        now = datetime.now(timezone.utc).replace(microsecond=0)
        for index, data in enumerate(DEMO_TICKETS):
            created_at = now - timedelta(hours=(index + 1) * 3)
            session.add(Ticket(**data, created_at=created_at))
        session.commit()
        return len(DEMO_TICKETS)


if __name__ == "__main__":
    create_tables()
    print(f"Inserted {seed_demo_tickets()} demo tickets.")
