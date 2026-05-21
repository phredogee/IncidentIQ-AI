# IncidentIQ-AI

[![CI](https://github.com/phredogee/IncidentIQ-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/phredogee/IncidentIQ-AI/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/demo-streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://incidentiq-ai.streamlit.app/)

AI-powered IT incident intelligence dashboard. Ingests support tickets, surfaces operational trends, detects volume anomalies, predicts severity for new tickets, and generates a Claude-written executive summary on demand.

**Live demo:** [incidentiq-ai.streamlit.app](https://incidentiq-ai.streamlit.app/)

---

## Features

- **LLM-written executive summary** — Claude (claude-opus-4-7) reads the filtered dataset and produces a stakeholder-ready narrative grounded in real numbers and ticket IDs.
- **Volume trend + anomaly detection** — daily ticket counts with a 14-day rolling-z-score baseline; spike days are flagged in red on the chart.
- **MTTR analytics** — overall median plus per-category breakdown (median, mean, resolved count).
- **Severity classifier** — TF-IDF + logistic regression trained on the dataset's description → severity mapping. Type a new incident, get a predicted class with per-class probabilities.
- **Similar incident detection** — cosine similarity over TF-IDF vectors to find the closest historical tickets.
- **Assignee workload** — open vs. resolved by tech, so leads can see who is overloaded.
- **Faceted filtering** — category, severity, status, assignee, free-text description search.

---

## Tech Stack

Python · Streamlit · Pandas · Plotly · scikit-learn · Anthropic Claude API

---

## Dashboard Preview

![Dashboard Overview](screenshots/dashboard-overview.png)
![Incident Table](screenshots/incident-table.png)
![Keyword Analysis](screenshots/keyword-analysis.png)

---

## Project Structure

```text
IncidentIQ-AI/
├── app.py                       # Streamlit entry point
├── src/
│   ├── analyzer.py              # Metrics, MTTR, daily volume, anomaly detection
│   ├── classifier.py            # TF-IDF + logistic regression severity model
│   ├── similarity.py            # TF-IDF cosine similarity search
│   └── summarizer.py            # Claude-powered executive summary (+ fallback)
├── scripts/
│   └── generate_incidents.py    # Synthetic dataset generator (1000 tickets)
├── data/
│   └── sample_incidents.csv     # Pre-generated dataset
├── tests/                       # pytest suite (analyzer / classifier / similarity / summarizer)
├── .github/workflows/ci.yml     # Tests on Python 3.11 + 3.12
├── Dockerfile                   # Container image for self-hosting
├── requirements.txt
└── requirements-dev.txt
```

---

## Getting Started

```bash
git clone git@github.com:phredogee/IncidentIQ-AI.git
cd IncidentIQ-AI
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Configure the Claude API key

The executive summary uses the Anthropic API. Without a key the app falls back to a templated summary.

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and paste your sk-ant-... key
```

You can also set `ANTHROPIC_API_KEY` in the environment instead.

### Run the dashboard

```bash
streamlit run app.py
```

### Regenerate the dataset (optional)

```bash
python scripts/generate_incidents.py
```

This produces a fresh, deterministic 1000-row dataset (seed `42`).

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=src
```

CI runs the suite on every push and pull request via GitHub Actions.

---

## Deploy

### Streamlit Community Cloud

1. Push to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo, and pick `app.py`.
3. In **Settings → Secrets**, paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
4. Deploy.

### Docker

```bash
docker build -t incidentiq-ai .
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=sk-ant-... incidentiq-ai
```

Then open `http://localhost:8501`.

---

## Architecture Notes

The model used for the executive summary is `claude-opus-4-7` with adaptive thinking (`effort: "low"`) — strong reasoning, kept snappy for an interactive dashboard. The summary call is wrapped in `@st.cache_data` keyed on the filter state so it only re-runs when the user actually changes what's being summarized.

The severity classifier is intentionally simple (TF-IDF + logistic regression with `class_weight="balanced"`) and trained at app boot via `@st.cache_resource`. Holdout accuracy on the synthetic dataset hovers around 45% across four classes — well above class-balanced baseline, and the misclassifications mostly stay in adjacent buckets (High↔Critical, Low↔Medium). On a real ITSM dataset with cleaner severity labels this approach typically reaches 65–75%.

Volume anomaly detection uses a 14-day rolling-mean baseline with z-score threshold 2.0. The injected spikes in the synthetic data (mid-March VPN outage, late-April email upgrade, late-June quarter-end access) all surface as anomalies.

---

## Status

Active development. Possible next steps:

- Sentence-transformer embeddings for higher-quality similar-incident search
- LLM-assisted root-cause clustering across spike windows
- Real-time ingestion from ServiceNow / Jira / PagerDuty webhooks
- Per-user authentication and tenant isolation

---

## License

MIT — see [LICENSE](LICENSE).
