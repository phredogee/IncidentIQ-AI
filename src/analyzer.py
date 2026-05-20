import pandas as pd
from collections import Counter
import re


def load_incidents(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def get_summary_metrics(df: pd.DataFrame) -> dict:
    return {
        "total_incidents": len(df),
        "open_incidents": len(df[df["status"].str.lower() == "open"]),
        "high_severity": len(df[df["severity"].str.lower() == "high"]),
        "resolved_incidents": len(df[df["status"].str.lower() == "resolved"]),
    }


def get_top_keywords(df: pd.DataFrame, top_n: int = 10):
    stopwords = {
        "the", "and", "to", "for", "in", "of", "with", "after",
        "not", "cannot", "unable", "user", "users", "report"
    }

    words = []

    for text in df["description"].dropna():
        cleaned = re.sub(r"[^a-zA-Z\s]", "", text.lower())
        words.extend([word for word in cleaned.split() if word not in stopwords and len(word) > 2])

    return Counter(words).most_common(top_n)
