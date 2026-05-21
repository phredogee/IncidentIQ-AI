import pandas as pd

from src.classifier import predict_severity, train_classifier


def _training_df():
    """Make a tiny but learnable dataset where description clearly signals severity."""
    rows = []
    for i in range(20):
        rows.extend(
            [
                {"description": "critical database outage all users", "severity": "Critical"},
                {"description": "anomalous login security alert", "severity": "Critical"},
                {"description": "vpn dropping for remote workers", "severity": "High"},
                {"description": "user cannot send email", "severity": "Medium"},
                {"description": "printer low toner color", "severity": "Low"},
            ]
        )
    return pd.DataFrame(rows)


def test_classifier_trains_and_predicts():
    model = train_classifier(_training_df(), test_size=0.2)
    assert model.accuracy > 0.5  # learnable dataset should be easy
    assert set(model.classes_) == {"Critical", "High", "Medium", "Low"}


def test_predict_severity_returns_probabilities():
    model = train_classifier(_training_df(), test_size=0.2)
    label, probs = predict_severity(model, "critical database outage")
    assert label in {"Critical", "High", "Medium", "Low"}
    assert abs(sum(probs.values()) - 1.0) < 1e-6
    assert all(0 <= p <= 1 for p in probs.values())


def test_predict_empty_text_returns_zero_probs():
    model = train_classifier(_training_df(), test_size=0.2)
    label, probs = predict_severity(model, "   ")
    assert label == ""
    assert all(p == 0.0 for p in probs.values())


def test_predict_picks_critical_for_outage():
    model = train_classifier(_training_df(), test_size=0.2)
    label, _ = predict_severity(model, "database outage affecting all users")
    assert label == "Critical"


def test_predict_picks_low_for_printer():
    model = train_classifier(_training_df(), test_size=0.2)
    label, _ = predict_severity(model, "printer low toner")
    assert label == "Low"
