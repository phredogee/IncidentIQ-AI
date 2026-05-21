from datetime import datetime, timedelta

import pandas as pd
import pytest


def _row(i, category, severity, status, days_ago, mttr_h=24, desc="generic issue"):
    created = datetime(2025, 1, 1) + timedelta(days=days_ago)
    resolved = (
        created + timedelta(hours=mttr_h)
        if status in {"Resolved", "Closed"}
        else pd.NaT
    )
    return {
        "ticket_id": f"INC{i:05d}",
        "created_at": created,
        "resolved_at": resolved,
        "category": category,
        "severity": severity,
        "status": status,
        "description": desc,
        "assignee": f"tech{(i % 3) + 1}",
    }


@pytest.fixture
def sample_df() -> pd.DataFrame:
    rows = [
        _row(1, "Network", "High", "Closed", 0, mttr_h=4, desc="VPN outage for remote users"),
        _row(2, "Network", "Medium", "Closed", 1, mttr_h=12, desc="Wi-Fi drops in Building A"),
        _row(3, "Email", "Low", "Closed", 2, mttr_h=48, desc="Outlook freezes opening attachments"),
        _row(4, "Email", "Medium", "Resolved", 3, mttr_h=20, desc="Cannot send large attachment"),
        _row(5, "Hardware", "Low", "Open", 5, desc="Battery drains quickly"),
        _row(6, "Hardware", "Low", "Closed", 6, mttr_h=72, desc="Docking station monitor issue"),
        _row(7, "Access", "Critical", "Closed", 7, mttr_h=2, desc="Service account credentials expired"),
        _row(8, "Access", "Medium", "In Progress", 8, desc="New hire cannot access shared drive"),
        _row(9, "Security", "Critical", "Closed", 9, mttr_h=1, desc="Anomalous login from foreign IP"),
        _row(10, "Printing", "Low", "Closed", 10, mttr_h=96, desc="Color printer low toner"),
    ]
    return pd.DataFrame(rows)
