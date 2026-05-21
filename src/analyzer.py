import re
from collections import Counter

import numpy as np
import pandas as pd


_DATE_COLS = ("created_at", "resolved_at")


def load_incidents(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    for col in _DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def get_summary_metrics(df: pd.DataFrame) -> dict:
    status = df["status"].str.lower()
    return {
        "total_incidents": len(df),
        "open_incidents": int((status == "open").sum()),
        "in_progress_incidents": int((status == "in progress").sum()),
        "resolved_incidents": int(status.isin({"resolved", "closed"}).sum()),
        "high_severity": int((df["severity"].str.lower() == "high").sum()),
        "critical_severity": int((df["severity"].str.lower() == "critical").sum()),
    }


def get_top_keywords(df: pd.DataFrame, top_n: int = 10):
    stopwords = {
        "the", "and", "to", "for", "in", "of", "with", "after",
        "not", "cannot", "unable", "user", "users", "report",
        "from", "during", "external", "internal", "machines",
    }

    words = []
    for text in df["description"].dropna():
        cleaned = re.sub(r"[^a-zA-Z\s]", "", text.lower())
        words.extend([w for w in cleaned.split() if w not in stopwords and len(w) > 2])
    return Counter(words).most_common(top_n)


def compute_mttr_hours(df: pd.DataFrame) -> pd.Series:
    """Per-row resolution time in hours. NaN where not yet resolved."""
    if "resolved_at" not in df.columns or "created_at" not in df.columns:
        return pd.Series(dtype=float)
    if df.empty:
        return pd.Series(dtype=float)
    resolved = pd.to_datetime(df["resolved_at"], errors="coerce")
    created = pd.to_datetime(df["created_at"], errors="coerce")
    delta = resolved - created
    return delta.dt.total_seconds() / 3600.0


def mttr_summary(df: pd.DataFrame) -> dict:
    mttr = compute_mttr_hours(df).dropna()
    if mttr.empty:
        return {"median_hours": None, "mean_hours": None, "p90_hours": None}
    return {
        "median_hours": float(mttr.median()),
        "mean_hours": float(mttr.mean()),
        "p90_hours": float(mttr.quantile(0.9)),
    }


def mttr_by_category(df: pd.DataFrame) -> pd.DataFrame:
    mttr = compute_mttr_hours(df)
    grouped = (
        df.assign(_mttr=mttr)
        .dropna(subset=["_mttr"])
        .groupby("category")["_mttr"]
        .agg(["median", "mean", "count"])
        .reset_index()
        .rename(columns={"median": "median_hours", "mean": "mean_hours", "count": "resolved_count"})
        .sort_values("median_hours", ascending=False)
    )
    return grouped


def daily_volume(df: pd.DataFrame) -> pd.DataFrame:
    if "created_at" not in df.columns:
        return pd.DataFrame(columns=["date", "count"])
    counts = (
        df.dropna(subset=["created_at"])
        .set_index("created_at")
        .resample("D")
        .size()
        .rename("count")
        .reset_index()
        .rename(columns={"created_at": "date"})
    )
    return counts


def detect_volume_anomalies(daily: pd.DataFrame, z_threshold: float = 2.0) -> pd.DataFrame:
    """Flag days whose count is z_threshold std devs above the rolling baseline."""
    if daily.empty:
        return daily.assign(z_score=[], is_anomaly=[])
    counts = daily["count"].astype(float)
    # Rolling 14-day baseline, shifted so the day under test isn't part of its own mean.
    baseline = counts.rolling(window=14, min_periods=5).mean().shift(1)
    spread = counts.rolling(window=14, min_periods=5).std().shift(1)
    z = (counts - baseline) / spread.replace(0, np.nan)
    return daily.assign(z_score=z, is_anomaly=(z >= z_threshold).fillna(False))


def assignee_workload(df: pd.DataFrame) -> pd.DataFrame:
    if "assignee" not in df.columns:
        return pd.DataFrame(columns=["assignee", "open", "resolved", "total"])
    status_lower = df["status"].str.lower()
    grouped = pd.DataFrame(
        {
            "assignee": df["assignee"],
            "open": status_lower.isin({"open", "in progress"}).astype(int),
            "resolved": status_lower.isin({"resolved", "closed"}).astype(int),
        }
    )
    workload = grouped.groupby("assignee").sum().reset_index()
    workload["total"] = workload["open"] + workload["resolved"]
    return workload.sort_values("total", ascending=False)
