"""Generate a synthetic but realistic incident dataset.

Output columns: ticket_id, created_at, resolved_at, category, severity,
status, description, assignee.

Designed so the dashboard shows interesting signal: category-specific MTTR
spreads, a multi-day VPN outage spike, an email-server upgrade weekend, and
gradually-ramping Access tickets near "quarter end". Reproducible via the
seed at the top.
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
N_INCIDENTS = 1000
START_DATE = datetime(2025, 1, 1, 8, 0, 0)
END_DATE = datetime(2025, 6, 30, 18, 0, 0)
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_incidents.csv"

CATEGORY_WEIGHTS = {
    "Network": 22,
    "Email": 15,
    "Access": 18,
    "Hardware": 14,
    "Software": 15,
    "Security": 6,
    "Telephony": 5,
    "Printing": 5,
}

# Category-specific severity profiles produce a learnable signal for the
# severity classifier — printer issues are mostly Low, security alerts skew High.
SEVERITY_BY_CATEGORY = {
    "Network":   {"Low": 15, "Medium": 35, "High": 35, "Critical": 15},
    "Email":     {"Low": 25, "Medium": 50, "High": 20, "Critical":  5},
    "Access":    {"Low": 30, "Medium": 45, "High": 20, "Critical":  5},
    "Hardware":  {"Low": 50, "Medium": 35, "High": 12, "Critical":  3},
    "Software":  {"Low": 30, "Medium": 45, "High": 20, "Critical":  5},
    "Security":  {"Low":  5, "Medium": 25, "High": 45, "Critical": 25},
    "Telephony": {"Low": 40, "Medium": 45, "High": 13, "Critical":  2},
    "Printing":  {"Low": 70, "Medium": 25, "High":  4, "Critical":  1},
}

ASSIGNEES = [
    "alice.chen",
    "bob.rivera",
    "carla.singh",
    "deepak.patel",
    "eva.morales",
    "frank.olsson",
    "grace.kim",
    "henry.nakamura",
]

# Average resolution time in hours, by severity.
MTTR_HOURS = {"Critical": 3, "High": 8, "Medium": 28, "Low": 96}

DESCRIPTION_TEMPLATES = {
    "Network": [
        "VPN disconnects every {n} minutes for remote users in {region}",
        "Wi-Fi drops in Building {bldg} during peak hours",
        "Slow network performance reported on {floor} floor",
        "Cannot reach internal site {site} from remote network",
        "DNS resolution failing intermittently for {region} users",
        "Switch port flapping on rack {rack}, multiple users affected",
        "VLAN tagging issue preventing access to {site} subnet",
    ],
    "Email": [
        "Outlook freezes when opening attachments larger than {n}MB",
        "Cannot send email with large attachment to external domain",
        "Calendar invites from external senders not appearing in inbox",
        "Distribution list {site}-team not receiving messages",
        "Email delivery delayed by {n} hours to external recipients",
        "Mailbox quota exceeded warning for {region} users",
        "Shared mailbox permissions reset after migration",
    ],
    "Access": [
        "New employee cannot access required systems on first day",
        "Employee unable to access shared drive after department transfer",
        "MFA prompt loop preventing login to {site} portal",
        "Password reset link not delivered to corporate email",
        "Role permissions revoked unexpectedly for {region} team",
        "SSO token expired prematurely, users locked out of {site}",
        "Service account credentials expired, batch job failing",
    ],
    "Hardware": [
        "User laptop battery drains within {n} hours of unplugging",
        "Docking station not recognizing external monitor",
        "Keyboard unresponsive after sleep wake on Building {bldg} machines",
        "Hard drive SMART failure warning on workstation {rack}",
        "Webcam not detected after latest OS update",
        "Mouse cursor stutters on {region} office laptops",
        "Headset audio cuts out during calls on docked machines",
    ],
    "Software": [
        "Application crashes after latest update on {floor} floor",
        "License server unreachable from {site} office",
        "Excel macros disabled after security patch",
        "PDF viewer hangs on documents larger than {n}MB",
        "Browser extensions blocked by new endpoint policy",
        "Database query timeout from {site} reporting tool",
        "Update rollout failing on Windows 11 {region} machines",
    ],
    "Security": [
        "Phishing email reported by {region} team, possible click-through",
        "Endpoint protection alert on workstation {rack}",
        "Anomalous login from foreign IP for {site} account",
        "USB device blocked by DLP policy, user requests exception",
        "Suspicious outbound traffic detected from {floor} floor segment",
    ],
    "Telephony": [
        "Softphone audio one-way for {region} remote employees",
        "Conference room phone in Building {bldg} not registering",
        "Call quality degraded during peak hours on SIP trunk",
        "Voicemail-to-email transcription failing for {site}",
        "Phone extension {n} ringing wrong desk after move",
    ],
    "Printing": [
        "Printer in Building {bldg} stuck in queue, jobs not releasing",
        "Color printer on {floor} floor reporting low toner repeatedly",
        "Network printer offline after firmware update",
        "Driver mismatch preventing printing from {region} laptops",
        "Badge release printer not authenticating users",
    ],
}

REGIONS = ["EMEA", "APAC", "NA-East", "NA-West", "LATAM"]
SITES = ["finance", "ops", "engineering", "hr", "sales"]


_SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]

# Keyword → severity nudge (number of steps up or down).
# Models the reality that incident wording carries severity signal.
_KEYWORD_SEVERITY_NUDGES = {
    # Escalators
    "outage": +2,
    "down": +1,
    "multiple users": +2,
    "all users": +2,
    "anomalous": +2,
    "phishing": +2,
    "suspicious": +1,
    "smart failure": +2,
    "service account": +1,
    "license server": +1,
    "database": +1,
    "locked out": +1,
    "delivery delayed": +1,
    "credentials expired": +1,
    # De-escalators
    "low toner": -2,
    "stuck in queue": -1,
    "battery drains": -1,
    "headset": -1,
    "voicemail": -1,
    "ringing wrong": -1,
    "extension": -1,
    "color printer": -1,
    "badge release": -1,
}


def _weighted(rng: random.Random, weights: dict[str, int]) -> str:
    keys, vals = zip(*weights.items())
    return rng.choices(keys, weights=vals, k=1)[0]


def _nudge_severity(severity: str, description: str, rng: random.Random) -> str:
    """Shift severity up/down based on description keywords (with some noise)."""
    text = description.lower()
    nudge = 0
    for keyword, delta in _KEYWORD_SEVERITY_NUDGES.items():
        if keyword in text:
            nudge += delta
    if nudge == 0:
        return severity
    # Apply 70% of the time so the signal is strong but not deterministic.
    if rng.random() > 0.7:
        return severity
    idx = _SEVERITY_ORDER.index(severity) + nudge
    idx = max(0, min(len(_SEVERITY_ORDER) - 1, idx))
    return _SEVERITY_ORDER[idx]


def _fill(template: str, rng: random.Random) -> str:
    return template.format(
        n=rng.choice([2, 5, 10, 15, 30, 60]),
        region=rng.choice(REGIONS),
        site=rng.choice(SITES),
        bldg=rng.choice(["A", "B", "C", "D"]),
        floor=rng.choice(["3rd", "4th", "5th", "ground"]),
        rack=f"R{rng.randint(1, 40):02d}",
    )


def _pick_status(created_at: datetime, severity: str, rng: random.Random) -> tuple[str, datetime | None]:
    age_hours = (END_DATE - created_at).total_seconds() / 3600
    mean_mttr = MTTR_HOURS[severity]
    mttr = max(0.25, rng.lognormvariate(mu=0, sigma=0.6) * mean_mttr)

    if age_hours > mttr:
        resolved_at = created_at + timedelta(hours=mttr)
        status = "Closed" if rng.random() < 0.7 else "Resolved"
        return status, resolved_at

    if age_hours > mttr * 0.3:
        return "In Progress", None
    return "Open", None


def _generate_baseline_timestamps(rng: random.Random) -> list[datetime]:
    """Spread incidents across the window with weekday bias."""
    total_seconds = int((END_DATE - START_DATE).total_seconds())
    timestamps: list[datetime] = []
    while len(timestamps) < N_INCIDENTS:
        offset = rng.randint(0, total_seconds)
        ts = START_DATE + timedelta(seconds=offset)
        if ts.weekday() >= 5 and rng.random() < 0.65:
            continue
        if ts.hour < 7 or ts.hour > 19:
            if rng.random() < 0.7:
                continue
        timestamps.append(ts)
    return timestamps


def _inject_spike(timestamps: list[datetime], center: datetime, count: int, spread_hours: int, rng: random.Random) -> None:
    """Replace `count` existing timestamps with ones clustered around `center`."""
    indices = rng.sample(range(len(timestamps)), count)
    for i in indices:
        delta = rng.uniform(-spread_hours, spread_hours)
        timestamps[i] = center + timedelta(hours=delta)


def generate(output_path: Path = OUTPUT_PATH) -> Path:
    rng = random.Random(SEED)
    timestamps = _generate_baseline_timestamps(rng)

    # Spike 1: multi-day VPN outage in mid-March.
    _inject_spike(timestamps, datetime(2025, 3, 12, 10, 0), count=55, spread_hours=36, rng=rng)
    # Spike 2: email server upgrade weekend in late April.
    _inject_spike(timestamps, datetime(2025, 4, 26, 14, 0), count=35, spread_hours=24, rng=rng)
    # Spike 3: quarter-end access requests in June.
    _inject_spike(timestamps, datetime(2025, 6, 27, 12, 0), count=40, spread_hours=72, rng=rng)

    timestamps.sort()

    rows: list[dict[str, str]] = []
    for i, created_at in enumerate(timestamps, start=1):
        # Bias categories on spike days.
        if datetime(2025, 3, 10) <= created_at <= datetime(2025, 3, 15) and rng.random() < 0.7:
            category = "Network"
        elif datetime(2025, 4, 25) <= created_at <= datetime(2025, 4, 28) and rng.random() < 0.65:
            category = "Email"
        elif datetime(2025, 6, 25) <= created_at <= datetime(2025, 6, 30) and rng.random() < 0.55:
            category = "Access"
        else:
            category = _weighted(rng, CATEGORY_WEIGHTS)

        severity = _weighted(rng, SEVERITY_BY_CATEGORY[category])
        # Spike incidents skew higher severity.
        if datetime(2025, 3, 10) <= created_at <= datetime(2025, 3, 15) and category == "Network":
            severity = rng.choices(["High", "Critical", "Medium"], weights=[5, 3, 2])[0]

        template = rng.choice(DESCRIPTION_TEMPLATES[category])
        description = _fill(template, rng)
        severity = _nudge_severity(severity, description, rng)
        status, resolved_at = _pick_status(created_at, severity, rng)
        assignee = rng.choice(ASSIGNEES)

        rows.append(
            {
                "ticket_id": f"INC{i:05d}",
                "created_at": created_at.isoformat(timespec="seconds"),
                "resolved_at": resolved_at.isoformat(timespec="seconds") if resolved_at else "",
                "category": category,
                "severity": severity,
                "status": status,
                "description": description,
                "assignee": assignee,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return output_path


if __name__ == "__main__":
    path = generate()
    print(f"Wrote {N_INCIDENTS} incidents to {path}")
