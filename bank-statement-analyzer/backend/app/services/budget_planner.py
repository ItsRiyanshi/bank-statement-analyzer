"""
Calendar-aware, adaptive rest-of-month budget planner.

Given: remaining days in the month, current balance, upcoming calendar
events with an estimated cost each, and historical spend patterns --
produce a per-day discretionary budget for the rest of the month, so
that event days get a bigger allowance and non-event days automatically
absorb the difference (the "Dynamic Rebalancing Algorithm" from the deck).
"""
from datetime import date, timedelta
from typing import List, Dict
from app.services.forecaster import average_daily_spend_by_weekday
from app.services.safe_to_spend import compute_current_balance, SAFETY_BUFFER_RATIO


def _last_day_of_month(d: date) -> date:
    if d.month == 12:
        nxt = date(d.year + 1, 1, 1)
    else:
        nxt = date(d.year, d.month + 1, 1)
    return nxt - timedelta(days=1)


def plan_rest_of_month(
    transactions: List[Dict],
    calendar_events: List[Dict],  # [{date, title, estimated_cost}]
    today: date,
    known_balance: float = None,
) -> List[Dict]:
    balance = compute_current_balance(transactions, known_balance)
    buffer = balance * SAFETY_BUFFER_RATIO
    last_day = _last_day_of_month(today)

    remaining_days = [today + timedelta(days=i) for i in range((last_day - today).days + 1)]
    events_by_day = {}
    for e in calendar_events:
        events_by_day.setdefault(e["date"], []).append(e)

    weekday_avg = average_daily_spend_by_weekday(transactions)

    # 1. Base allocation: whatever's left after buffer, spread evenly first
    event_total = sum(e["estimated_cost"] for evs in events_by_day.values() for e in evs)
    spendable_pool = max(0.0, balance - buffer - event_total)
    base_daily = spendable_pool / len(remaining_days) if remaining_days else 0.0

    plan = []
    for d in remaining_days:
        day_events = events_by_day.get(d, [])
        event_cost = sum(e["estimated_cost"] for e in day_events)

        # Days with events get their event cost PLUS a share of the base
        # allowance (using the historical weekday average as a weight so
        # e.g. weekends still get relatively more than weekdays).
        weight = weekday_avg.get(d.weekday(), base_daily) or base_daily
        planned = event_cost + max(base_daily, weight * 0.6)

        reason = None
        if day_events:
            titles = ", ".join(e["title"] for e in day_events)
            reason = f"Includes estimated cost for: {titles}"

        plan.append(
            {
                "day": d,
                "planned_amount": round(planned, 2),
                "reason": reason,
                "has_event": bool(day_events),
            }
        )

    # 2. Rebalance: if total planned exceeds spendable pool + events, scale
    #    down non-event days proportionally so we never plan beyond balance.
    total_planned = sum(p["planned_amount"] for p in plan)
    max_allowed = spendable_pool + event_total
    if total_planned > max_allowed and max_allowed > 0:
        scale = max_allowed / total_planned
        for p in plan:
            p["planned_amount"] = round(p["planned_amount"] * scale, 2)

    return plan