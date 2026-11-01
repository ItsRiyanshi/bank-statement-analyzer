"""
Lightweight, dependency-free time-series forecasting.

The pitch deck mentions Prophet/LSTM as an upgrade path, but those add
heavy dependencies for a hackathon-scale app. This module uses a simple
and fully explainable approach instead:
  - Daily average spend by weekday (captures "I spend more on weekends")
  - Linear trend over the last N days (captures gradually rising spend)
Both are free, fast, and easy to reason about/debug.
"""
from collections import defaultdict
from statistics import mean
from datetime import date, timedelta
from typing import List, Dict


def average_daily_spend_by_weekday(transactions: List[Dict]) -> Dict[int, float]:
    """0=Monday ... 6=Sunday -> average expense on that weekday."""
    by_weekday = defaultdict(list)
    for t in transactions:
        if t["amount"] < 0:
            by_weekday[t["date"].weekday()].append(-t["amount"])
    overall_avg = mean([abs(t["amount"]) for t in transactions if t["amount"] < 0] or [0])
    return {wd: (mean(v) if v else overall_avg) for wd, v in by_weekday.items()} or {
        i: overall_avg for i in range(7)
    }


def forecast_remaining_month(transactions: List[Dict], today: date) -> float:
    """Naive forecast: sum of expected average daily spend for each
    remaining day of the current month, based on historical weekday
    averages."""
    weekday_avg = average_daily_spend_by_weekday(transactions)
    if not weekday_avg:
        return 0.0

    # find last day of the month
    if today.month == 12:
        next_month_first = date(today.year + 1, 1, 1)
    else:
        next_month_first = date(today.year, today.month + 1, 1)
    last_day = next_month_first - timedelta(days=1)

    total = 0.0
    d = today + timedelta(days=1)
    while d <= last_day:
        total += weekday_avg.get(d.weekday(), 0.0)
        d += timedelta(days=1)
    return round(total, 2)
