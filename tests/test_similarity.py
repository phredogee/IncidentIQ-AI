from src.similarity import find_similar_incidents


def test_similar_incidents_returns_top_n(sample_df):
    df = sample_df.reset_index(drop=True)
    result = find_similar_incidents(df, "INC00001", top_n=3)
    assert len(result) <= 3
    assert "INC00001" not in result["ticket_id"].values


def test_similar_incidents_finds_related_vpn_to_wifi(sample_df):
    # Both INC00001 (VPN) and INC00002 (Wi-Fi) are Network — expect similarity.
    df = sample_df.reset_index(drop=True)
    result = find_similar_incidents(df, "INC00001", top_n=5)
    assert "INC00002" in result["ticket_id"].values


def test_similar_incidents_unknown_ticket_returns_empty(sample_df):
    result = find_similar_incidents(sample_df.reset_index(drop=True), "NONEXISTENT")
    assert result.empty


def test_similar_incidents_scores_are_bounded(sample_df):
    df = sample_df.reset_index(drop=True)
    result = find_similar_incidents(df, "INC00001", top_n=3)
    assert (result["similarity_score"] >= 0).all()
    assert (result["similarity_score"] <= 1).all()
