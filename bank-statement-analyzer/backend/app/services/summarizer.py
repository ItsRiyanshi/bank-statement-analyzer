"""
Generates plain-English, explainable summaries from computed analytics.
No LLM API call required -- built from template + numbers, which keeps
it free, fast, and 100% accurate to the underlying data (no hallucination
risk), matching the "Explainable summaries" requirement in the deck.
"""
from typing import Dict, List


def generate_monthly_summary(analytics: Dict, health: Dict) -> str:
    top_category = max(analytics["by_category"].items(), key=lambda kv: kv[1], default=(None, 0))
    lines = [
        f"This month you earned ₹{analytics['total_income']:,.2f} and spent ₹{analytics['total_expense']:,.2f}, "
        f"leaving a net of ₹{analytics['net']:,.2f}.",
    ]
    if top_category[0]:
        lines.append(f"Your biggest spending category was {top_category[0]} at ₹{top_category[1]:,.2f}.")
    lines.append(f"Your financial health score is {health['score']}/100 ({health['grade']}).")
    if health["tips"]:
        lines.append(health["tips"][0])
    return " ".join(lines)
