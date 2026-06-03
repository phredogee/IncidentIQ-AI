import io
import os

import streamlit as st
import pandas as pd
import plotly.express as px

from src.analyzer import (
    assignee_workload,
    daily_volume,
    detect_volume_anomalies,
    get_summary_metrics,
    get_top_keywords,
    load_incidents,
    mttr_by_category,
    mttr_summary,
)
from src.classifier import predict_severity, train_classifier
from src.summarizer import generate_executive_summary
from src.similarity import find_similar_incidents

st.set_page_config(
    page_title="IncidentIQ-AI",
    page_icon="🧠",
    layout="wide"
)

# Forward Streamlit secrets into the env so the Deepseek client picks them up
# both locally (.streamlit/secrets.toml) and on Streamlit Community Cloud.
try:
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    if api_key:
        os.environ["DEEPSEEK_API_KEY"] = api_key
except Exception:
    pass

# Remove the old @st.cache_data line 38 completely
def _cached_summary(metrics, top_category, top_severity, top_keywords, sample_csv):
    sample_df = pd.read_csv(io.StringIO(sample_csv))
    return generate_executive_summary(metrics, top_category, top_severity, top_keywords, sample_csv)

@st.cache_resource(show_spinner="Training severity classifier…")
def _train_classifier(data_csv: str):
    return train_classifier(pd.read_csv(io.StringIO(data_csv)))

st.title("IncidentIQ-AI")
st.subheader("AI-Powered IT Incident Intelligence Dashboard")

st.write(
    "Upload or analyze incident tickets to identify operational trends, recurring issues, "
    "and high-priority support patterns."
)

uploaded_file = st.file_uploader("Upload incident CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    for col in ("created_at", "resolved_at"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
else:
    df = load_incidents("data/sample_incidents.csv")

st.divider()

metrics = get_summary_metrics(df)
mttr = mttr_summary(df)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Incidents", metrics["total_incidents"])
col2.metric("Open", metrics["open_incidents"] + metrics["in_progress_incidents"])
col3.metric("High Severity", metrics["high_severity"])
col4.metric("Critical", metrics["critical_severity"])
col5.metric(
    "Median MTTR (hrs)",
    f"{mttr['median_hours']:.1f}" if mttr["median_hours"] is not None else "—",
)

st.sidebar.header("Filters")

selected_categories = st.sidebar.multiselect(
    "Category",
    options=sorted(df["category"].unique()),
    default=sorted(df["category"].unique())
)

selected_severities = st.sidebar.multiselect(
    "Severity",
    options=sorted(df["severity"].unique()),
    default=sorted(df["severity"].unique())
)

selected_statuses = st.sidebar.multiselect(
    "Status",
    options=sorted(df["status"].unique()),
    default=sorted(df["status"].unique())
)

if "assignee" in df.columns:
    selected_assignees = st.sidebar.multiselect(
        "Assignee",
        options=sorted(df["assignee"].dropna().unique()),
        default=sorted(df["assignee"].dropna().unique()),
    )
else:
    selected_assignees = None

search_term = st.sidebar.text_input("Search incident descriptions")

filtered_df = df[
    (df["category"].isin(selected_categories)) &
    (df["severity"].isin(selected_severities)) &
    (df["status"].isin(selected_statuses))
]
if selected_assignees is not None:
    filtered_df = filtered_df[filtered_df["assignee"].isin(selected_assignees)]

if search_term:
    filtered_df = filtered_df[
        filtered_df["description"].str.contains(search_term, case=False, na=False)
    ]

if filtered_df.empty:
    st.warning("No incidents match the selected filters.")
    st.stop()

st.divider()

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Incidents by Category")
    category_counts = filtered_df["category"].value_counts().reset_index()
    category_counts.columns = ["Category", "Count"]

    fig_category = px.bar(
        category_counts,
        x="Category",
        y="Count",
        title="Ticket Volume by Category"
    )

    st.plotly_chart(fig_category, use_container_width=True)

with right_col:
    st.subheader("Incidents by Severity")
    severity_counts = filtered_df["severity"].value_counts().reset_index()
    severity_counts.columns = ["Severity", "Count"]

    fig_severity = px.pie(
        severity_counts,
        names="Severity",
        values="Count",
        title="Ticket Severity Distribution"
    )

    st.plotly_chart(fig_severity, use_container_width=True)

if "created_at" in filtered_df.columns and filtered_df["created_at"].notna().any():
    st.divider()
    st.subheader("Incident Volume Over Time")
    daily = daily_volume(filtered_df)
    daily = detect_volume_anomalies(daily)

    fig_trend = px.line(daily, x="date", y="count", title="Tickets Created per Day")
    anomalies = daily[daily["is_anomaly"]]
    if not anomalies.empty:
        fig_trend.add_scatter(
            x=anomalies["date"],
            y=anomalies["count"],
            mode="markers",
            marker=dict(color="red", size=10, symbol="circle-open", line=dict(width=2)),
            name="Anomaly",
            hovertemplate="%{x|%Y-%m-%d}<br>%{y} tickets<extra></extra>",
        )
    st.plotly_chart(fig_trend, use_container_width=True)

    if not anomalies.empty:
        anomaly_summary = (
            anomalies[["date", "count", "z_score"]]
            .assign(date=lambda d: d["date"].dt.strftime("%Y-%m-%d"))
            .rename(columns={"date": "Date", "count": "Tickets", "z_score": "Z-score"})
        )
        with st.expander(f"{len(anomalies)} anomalous days detected"):
            st.dataframe(anomaly_summary, use_container_width=True, hide_index=True)

if "resolved_at" in filtered_df.columns and filtered_df["resolved_at"].notna().any():
    st.divider()
    st.subheader("Mean Time to Resolve")
    mttr_left, mttr_right = st.columns(2)
    with mttr_left:
        mttr_cat = mttr_by_category(filtered_df)
        fig_mttr = px.bar(
            mttr_cat,
            x="category",
            y="median_hours",
            title="Median MTTR by Category (hours)",
            hover_data=["mean_hours", "resolved_count"],
        )
        st.plotly_chart(fig_mttr, use_container_width=True)
    with mttr_right:
        if "assignee" in filtered_df.columns:
            workload = assignee_workload(filtered_df)
            fig_workload = px.bar(
                workload,
                x="assignee",
                y=["open", "resolved"],
                title="Assignee Workload",
                labels={"value": "Tickets", "variable": "Status"},
            )
            st.plotly_chart(fig_workload, use_container_width=True)

st.divider()

st.subheader("Recurring Issue Keywords")

top_keywords = get_top_keywords(df)

keyword_df = pd.DataFrame(top_keywords, columns=["Keyword", "Count"])

st.dataframe(keyword_df, use_container_width=True)

st.divider()

st.subheader("Predict Severity for a New Incident")
st.caption(
    "Trained on this dataset's description → severity mapping. "
    "Useful for first-pass triage before a human review."
)

classifier_model = _train_classifier(df.to_csv(index=False))
predict_left, predict_right = st.columns([3, 1])
with predict_left:
    new_incident_text = st.text_area(
        "Describe the incident",
        placeholder="e.g. VPN dropping for remote users every 10 minutes",
        height=100,
    )
with predict_right:
    st.metric("Model accuracy (holdout)", f"{classifier_model.accuracy:.0%}")
    st.metric("Training rows", len(df))

if new_incident_text.strip():
    predicted_label, probs = predict_severity(classifier_model, new_incident_text)
    prob_df = (
        pd.DataFrame({"Severity": list(probs.keys()), "Probability": list(probs.values())})
        .sort_values("Probability", ascending=False)
        .reset_index(drop=True)
    )
    pred_col, prob_col = st.columns([1, 2])
    with pred_col:
        st.metric("Predicted severity", predicted_label)
    with prob_col:
        fig_probs = px.bar(
            prob_df,
            x="Severity",
            y="Probability",
            title="Class probabilities",
            range_y=[0, 1],
        )
        st.plotly_chart(fig_probs, use_container_width=True)

st.divider()

st.subheader("Similar Incident Detection")

selected_ticket = st.selectbox(
    "Select an incident to find similar tickets",
    options=filtered_df["ticket_id"].tolist()
)

similar_incidents = find_similar_incidents(
    filtered_df.reset_index(drop=True),
    selected_ticket,
    top_n=3
)

if similar_incidents.empty:
    st.info("No similar incidents found.")
else:
    st.dataframe(
        similar_incidents[
            ["ticket_id", "category", "severity", "description", "status", "similarity_score"]
        ],
        use_container_width=True
    )
st.divider()

top_category = filtered_df["category"].value_counts().idxmax()
top_severity = filtered_df["severity"].value_counts().idxmax()

st.subheader("AI Executive Summary")
with st.spinner("Generating summary with DeepSeek"):
    summary = _cached_summary(
        metrics,
        top_category,
        top_severity,
        tuple(top_keywords),
        filtered_df.to_csv(index=False),
    )
st.info(summary)

st.divider()

st.subheader("Incident Data")
st.dataframe(filtered_df, use_container_width=True)
