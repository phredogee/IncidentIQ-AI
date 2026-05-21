"""TF-IDF + logistic regression severity classifier.

Trained on the incident description → severity mapping. Used by the dashboard
to predict severity for a new free-text incident before a human triages it.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


@dataclass
class TrainedClassifier:
    pipeline: Pipeline
    classes_: list[str]
    test_report: dict
    accuracy: float


def _build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    stop_words="english",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def train_classifier(df: pd.DataFrame, test_size: float = 0.2) -> TrainedClassifier:
    """Train on description → severity. Returns the fitted pipeline + holdout metrics."""
    data = df.dropna(subset=["description", "severity"])
    X = data["description"].astype(str)
    y = data["severity"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    pipeline = _build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    accuracy = float(report["accuracy"])
    classes = list(pipeline.named_steps["clf"].classes_)
    return TrainedClassifier(
        pipeline=pipeline,
        classes_=classes,
        test_report=report,
        accuracy=accuracy,
    )


def predict_severity(model: TrainedClassifier, text: str) -> tuple[str, dict[str, float]]:
    """Return predicted label and {class: probability}."""
    if not text.strip():
        return "", {c: 0.0 for c in model.classes_}
    probs = model.pipeline.predict_proba([text])[0]
    label = model.classes_[int(probs.argmax())]
    return label, {c: float(p) for c, p in zip(model.classes_, probs)}
