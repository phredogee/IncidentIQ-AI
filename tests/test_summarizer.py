import os

from src.summarizer import generate_summary


def test_summarizer_fallback_when_no_api_key(monkeypatch, sample_df):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    metrics = {
        "total_incidents": 10,
        "open_incidents": 1,
        "resolved_incidents": 8,
        "high_severity": 1,
    }
    summary = generate_summary(metrics, "Network", "High", [("vpn", 3), ("remote", 2)], sample_df)
    assert "ANTHROPIC_API_KEY" in summary
    assert "Network" in summary
    assert "High" in summary
    assert "10 incidents" in summary
