import pandas as pd

from src.analyzer import (
    assignee_workload,
    daily_volume,
    detect_volume_anomalies,
    get_summary_metrics,
    get_top_keywords,
    mttr_by_category,
    mttr_summary,
)


def test_summary_metrics_counts(sample_df):
    metrics = get_summary_metrics(sample_df)
    assert metrics["total_incidents"] == 10
    assert metrics["open_incidents"] == 1
    assert metrics["in_progress_incidents"] == 1
    assert metrics["resolved_incidents"] == 8
    assert metrics["high_severity"] == 1
    assert metrics["critical_severity"] == 2


def test_top_keywords_filters_stopwords(sample_df):
    keywords = dict(get_top_keywords(sample_df, top_n=20))
    # generic stopwords filtered
    assert "the" not in keywords
    assert "from" not in keywords
    # real terms present
    assert "vpn" in keywords or "outlook" in keywords or "remote" in keywords


def test_mttr_summary_only_counts_resolved(sample_df):
    summary = mttr_summary(sample_df)
    assert summary["median_hours"] is not None
    assert summary["median_hours"] > 0
    assert summary["p90_hours"] >= summary["median_hours"]


def test_mttr_summary_handles_empty_df():
    empty = pd.DataFrame(columns=["created_at", "resolved_at"])
    summary = mttr_summary(empty)
    assert summary["median_hours"] is None


def test_mttr_by_category_orders_descending(sample_df):
    table = mttr_by_category(sample_df)
    medians = table["median_hours"].tolist()
    assert medians == sorted(medians, reverse=True)
    assert (table["resolved_count"] > 0).all()


def test_daily_volume_groups_by_day(sample_df):
    daily = daily_volume(sample_df)
    assert {"date", "count"}.issubset(daily.columns)
    assert daily["count"].sum() == len(sample_df)


def test_anomaly_detection_returns_required_columns(sample_df):
    daily = daily_volume(sample_df)
    annotated = detect_volume_anomalies(daily)
    assert {"z_score", "is_anomaly"}.issubset(annotated.columns)
    # All bools after fillna
    assert annotated["is_anomaly"].dtype == bool


def test_assignee_workload_includes_all_techs(sample_df):
    workload = assignee_workload(sample_df)
    assert set(workload["assignee"]) == {"tech1", "tech2", "tech3"}
    assert (workload["total"] == workload["open"] + workload["resolved"]).all()
