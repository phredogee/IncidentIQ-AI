import streamlit as st
import pandas as pd
import plotly.express as px

from src.analyzer import load_incidents, get_summary_metrics, get_top_keywords
from src.summarizer import generate_summary
from src.similarity import find_similar_incidents

st.set_page_config(
    page_title="IncidentIQ-AI",
    page_icon="🧠",
    layout="wide"
)

st.title("IncidentIQ-AI")
st.subheader("AI-Powered IT Incident Intelligence Dashboard")

st.write(
    "Upload or analyze incident tickets to identify operational trends, recurring issues, "
    "and high-priority support patterns."
)

uploaded_file = st.file_uploader("Upload incident CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = load_incidents("data/sample_incidents.csv")

st.divider()

metrics = get_summary_metrics(df)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Incidents", metrics["total_incidents"])
col2.metric("Open Incidents", metrics["open_incidents"])
col3.metric("High Severity", metrics["high_severity"])
col4.metric("Resolved", metrics["resolved_incidents"])

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

search_term = st.sidebar.text_input("Search incident descriptions")

filtered_df = df[
    (df["category"].isin(selected_categories)) &
    (df["severity"].isin(selected_severities)) &
    (df["status"].isin(selected_statuses))
]

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

st.divider()

st.subheader("Recurring Issue Keywords")

top_keywords = get_top_keywords(df)

keyword_df = pd.DataFrame(top_keywords, columns=["Keyword", "Count"])

st.dataframe(keyword_df, use_container_width=True)

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

summary = generate_summary(metrics, top_category, top_severity, top_keywords)

st.subheader("AI-Style Executive Summary")
st.info(summary)

st.divider()

st.subheader("Incident Data")
st.dataframe(filtered_df, use_container_width=True)
