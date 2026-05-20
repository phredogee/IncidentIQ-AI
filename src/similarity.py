import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def find_similar_incidents(
    df: pd.DataFrame,
    selected_ticket_id: str,
    top_n: int = 3
) -> pd.DataFrame:
    if df.empty or "description" not in df.columns or "ticket_id" not in df.columns:
        return pd.DataFrame()

    if selected_ticket_id not in df["ticket_id"].values:
        return pd.DataFrame()

    descriptions = df["description"].fillna("")

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(descriptions)

    selected_index = df.index[df["ticket_id"] == selected_ticket_id][0]

    similarity_scores = cosine_similarity(
        tfidf_matrix[selected_index],
        tfidf_matrix
    ).flatten()

    results = df.copy()
    results["similarity_score"] = similarity_scores

    results = results[results["ticket_id"] != selected_ticket_id]

    results = results.sort_values(
        by="similarity_score",
        ascending=False
    ).head(top_n)

    results["similarity_score"] = results["similarity_score"].round(3)

    return results
