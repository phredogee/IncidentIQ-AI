import os
import anthropic
import pandas as pd


_SYSTEM_PROMPT = """You are an IT operations analyst reviewing incident ticket data for a leadership briefing.

Produce a concise executive summary (3–4 short paragraphs) that:
1. Characterizes the operational state — total volume, severity mix, open vs. resolved.
2. Identifies the dominant problem areas, grounded in the categories and recurring keywords.
3. Calls out specific high-severity patterns from the sample incidents — name the systems or symptoms.
4. Recommends 2–3 concrete next actions for the IT team.

Be specific. Reference actual numbers and ticket IDs where useful. Avoid generic platitudes like "monitor closely" or "improve processes" — every sentence should add information a stakeholder couldn't get from the dashboard at a glance."""


def generate_summary(
    metrics: dict,
    top_category: str,
    top_severity: str,
    top_keywords: list,
    sample_incidents: pd.DataFrame,
) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_summary(metrics, top_category, top_severity, top_keywords)

    client = anthropic.Anthropic(api_key=api_key)

    keywords_str = "\n".join(f"- {kw}: {count}" for kw, count in top_keywords[:10])
    high_sev = sample_incidents[
        sample_incidents["severity"].str.lower() == "high"
    ].head(8)
    if high_sev.empty:
        high_sev = sample_incidents.head(8)
    incidents_str = "\n".join(
        f"- [{row['ticket_id']}] {row['category']} / {row['status']}: {row['description']}"
        for _, row in high_sev.iterrows()
    )

    user_message = f"""Analyze this incident dataset:

**Metrics**
- Total: {metrics['total_incidents']}
- Open: {metrics['open_incidents']}
- Resolved: {metrics['resolved_incidents']}
- High severity: {metrics['high_severity']}

**Dominant category:** {top_category}
**Most frequent severity:** {top_severity}

**Recurring keywords (occurrences):**
{keywords_str}

**Representative incidents:**
{incidents_str}
"""

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        output_config={"effort": "low"},
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return next(block.text for block in response.content if block.type == "text")


def _fallback_summary(
    metrics: dict, top_category: str, top_severity: str, top_keywords: list
) -> str:
    keywords = ", ".join(kw for kw, _ in top_keywords[:5])
    return (
        "⚠️ No `ANTHROPIC_API_KEY` configured — showing a template summary. "
        "Set the key in `.streamlit/secrets.toml` (local) or in the Streamlit Cloud "
        "secrets panel to enable Claude-generated insights.\n\n"
        f"Analyzed {metrics['total_incidents']} incidents. "
        f"Most common category: **{top_category}**. Most frequent severity: **{top_severity}**. "
        f"{metrics['open_incidents']} open, {metrics['high_severity']} high severity. "
        f"Recurring keywords: {keywords}."
    )
