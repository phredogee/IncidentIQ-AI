# IncidentIQ-AI

[![CI](https://github.com/phredogee/IncidentIQ-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/phredogee/IncidentIQ-AI/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/demo-streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://incidentiq-ai.streamlit.app/)

AI-powered IT incident intelligence dashboard. Ingests support tickets, surfaces operational trends, detects volume anomalies, predicts severity for new tickets, and generates a DeepSeek-written executive summary on demand.

### -> [Open the live demo](https://incidentiq-ai.streamlit.app/)


## Features

- **LLM-written executive summary** - DeepSeek (deepseek-chat) reads the filtered dataset and produces a stakeholder-ready narrative grounded in real numbers and ticket IDs.
- **Volume trend + anomaly detection** - daily ticket counts with a 14-day rolling z-score baseline; spike days are flagged in red on the chart.
- **MTTR analytics** - overall median plus per-category breakdown (median, mean, resolved count).
- **Severity classifier** - TF-IDF + logistic regression trained on the dataset's description -> severity mapping. Type a new incident, get a predicted class with per-class probabilities.
- **Similar incident detection** - cosine similarity over TF-IDF vectors to find the closest historical tickets.
- **Assignee workload** - open vs. resolved by tech, so leads can see who is overloaded.
- **Faceted filtering** - category, severity, status, assignee, free-text description search.


## Tech Stack

Python · Streamlit · Pandas · Plotly · scikit-learn · DeepSeek API


## Dashboard Preview

![Dashboard Overview](screenshots/dashboard-overview.png)
![Incident Table](screenshots/incident-table.png)
![Keyword Analysis](screenshots/keyword-analysis.png)


## Project Structure

```text
IncidentIQ-AI/
├── app.py              # Streamlit entry point
├── src/
│   ├── analyzer.py     # Metrics, MTTR, daily volume, anomaly detection
│   ├── classifier.py   # TF-IDF + logistic regression severity model
│   ├── similarity.py   # TF-IDF cosine similarity search
│   └── summarizer.py   # DeepSeek-powered executive summary (+ fallback)
├── scripts/
│   └── generate_incidents.py  # Synthetic dataset generator (1000 tickets)
```
