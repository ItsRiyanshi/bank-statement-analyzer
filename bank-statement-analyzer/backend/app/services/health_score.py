"""
Computes a 0-100 "Financial Health Score" from a set of transactions,
using simple, explainable sub-metrics rather than a black box.

Sub-scores (each 0-100, then weighted):
  - savings_rate: (income - expense) / income
  - expense_stability: inverse of month-to-month expense volatility
  - recurring_burden: recurring payments as a % of income (lower is better)
  - anomaly_frequency: fraction of transactions flagged anomalous (lower better)
"""
from collections import defaultdict
from statistics import mean, pstdev
from typing import List, Dict


def _score_savings_rate(income: float, expense: float) -> float:
    if income <= 0:
        return 0
    rate = (income - expense) / income
    return max(0, min(100, rate * 200))  # 50% savings rate -> 100 pts


def _score_stability(monthly_expenses: List[float]) -> float:
    if len(monthly_expenses) < 2:
        return 70  # not enough history, neutral score
    m = mean(monthly_expenses) or 1
    volatility = pstdev(monthly_expenses) / m
    return max(0, min(100, 100 - volatility * 150))


def _score_recurring_burden(recurring_total: float, income: float) -> float:
    if income <= 0:
        return 50
    burden = recurring_total / income
    return max(0, min(100, 100 - burden * 150))


def _score_anomaly_freq(anomaly_count: int, total_count: int) -> float:
    if total_count == 0:
        return 100
    freq = anomaly_count / total_count
    return max(0, min(100, 100 - freq * 300))


def compute_health_score(transactions: List[Dict]) -> Dict:
    income = sum(t["amount"] for t in transactions if t["amount"] > 0)
    expense = sum(-t["amount"] for t in transactions if t["amount"] < 0)

    monthly = defaultdict(float)
    for t in transactions:
        if t["amount"] < 0:
            key = t["date"].strftime("%Y-%m")
            monthly[key] += -t["amount"]

    recurring_total = sum(-t["amount"] for t in transactions if t.get("is_recurring") and t["amount"] < 0)
    anomaly_count = sum(1 for t in transactions if t.get("is_anomaly"))

    savings_score = _score_savings_rate(income, expense)
    stability_score = _score_stability(list(monthly.values()))
    burden_score = _score_recurring_burden(recurring_total, income)
    anomaly_score = _score_anomaly_freq(anomaly_count, len(transactions))

    weights = {"savings": 0.35, "stability": 0.25, "burden": 0.2, "anomaly": 0.2}
    final = (
        savings_score * weights["savings"]
        + stability_score * weights["stability"]
        + burden_score * weights["burden"]
        + anomaly_score * weights["anomaly"]
    )
    final = round(final)

    if final >= 80:
        grade = "Excellent"
    elif final >= 60:
        grade = "Good"
    elif final >= 40:
        grade = "Fair"
    else:
        grade = "Needs Attention"

    tips = []
    if savings_score < 50:
        tips.append("Your expenses are close to (or above) your income -- try trimming discretionary spending.")
    if stability_score < 50:
        tips.append("Your monthly spending varies a lot -- building a fixed monthly budget could help.")
    if burden_score < 50:
        tips.append("Recurring payments (EMIs/subscriptions) take up a large share of income -- review subscriptions.")
    if anomaly_score < 50:
        tips.append("Several unusually large transactions were detected this period -- review them for accuracy.")
    if not tips:
        tips.append("Your finances look healthy -- keep maintaining this savings rate!")

    return {
        "score": final,
        "grade": grade,
        "breakdown": {
            "savings_rate": round(savings_score),
            "expense_stability": round(stability_score),
            "recurring_burden": round(burden_score),
            "anomaly_frequency": round(anomaly_score),
        },
        "tips": tips,
    }
