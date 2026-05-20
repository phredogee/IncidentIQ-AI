def generate_summary(metrics: dict, top_category: str, top_severity: str, top_keywords: list) -> str:
    keywords = ", ".join([word for word, count in top_keywords[:5]])

    return (
        f"IncidentIQ-AI analyzed {metrics['total_incidents']} incidents. "
        f"The most common incident category is {top_category}, while the most frequent severity level is {top_severity}. "
        f"There are currently {metrics['open_incidents']} open incidents and {metrics['high_severity']} high-severity incidents. "
        f"Recurring issue keywords include: {keywords}. "
        f"Recommended next step: review repeated network, access, or application-related issues for possible root cause trends."
    )
