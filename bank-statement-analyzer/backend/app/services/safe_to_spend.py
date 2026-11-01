"""
'Safe-to-Spend' engine.

Dynamically calculates how much money the user can safely spend without
jeopardizing essential financial commitments, recurring bills (EMIs, rent,
utilities, subscriptions), or risking overdraft.

Core model:
  available_balance = current closing balance from statement
  planning_period = days until next expected income or remaining days in cycle
  upcoming_obligations = scheduled bills / EMIs / events due in the planning period
  reserved_essentials = essential living spend (groceries, food, transport, medical)
  buffer = safety cushion (5% of balance)
  discretionary_funds = max(0, available_funds - upcoming_obligations - reserved_essentials - buffer)
  safe_to_spend_today = discretionary_funds / remaining_days
"""
from datetime import date, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from statistics import mean

ESSENTIAL_CATEGORIES = {
    "groceries",
    "food & dining",
    "transport",
    "health",
    "medical",
    "bills & utilities",
    "utilities",
}
SAFETY_BUFFER_RATIO = 0.05  # keep 5% of balance as a safety cushion


def compute_current_balance(
    transactions: List[Dict],
    known_balance: float = None,
) -> float:
    """
    Prefer the real closing balance parsed straight off a statement
    (known_balance) over summing transaction deltas from zero.
    """
    if known_balance is not None:
        return round(float(known_balance), 2)
    if not transactions:
        return 0.0
    return round(float(sum(t.get("amount", 0) for t in transactions)), 2)


def days_left_in_month(today: date) -> int:
    """Returns number of remaining days in current month including today."""
    if today.month == 12:
        next_month_first = date(today.year + 1, 1, 1)
    else:
        next_month_first = date(today.year, today.month + 1, 1)
    last_day = next_month_first - timedelta(days=1)
    return max(1, (last_day - today).days + 1)


def detect_recurring_income(
    transactions: List[Dict], ref_date: date
) -> Tuple[Optional[date], float, bool]:
    """
    Detects recurring regular income (salary, payroll, regular credits),
    its typical amount, and expected next income date.
    Returns: (next_income_date, typical_amount, is_upcoming_this_cycle)
    """
    rec_inc = [
        t for t in transactions
        if t.get("amount", 0) > 0 and t.get("is_recurring")
    ]
    if not rec_inc:
        rec_inc = [
            t for t in transactions
            if t.get("amount", 0) > 0 and t.get("category") == "Income"
        ]
    if not rec_inc:
        rec_inc = [
            t for t in transactions
            if t.get("amount", 0) >= 10000
        ]

    if not rec_inc:
        return None, 0.0, False

    typical_amt = round(float(mean(t["amount"] for t in rec_inc)), 2)
    day_counts = Counter(t["date"].day for t in rec_inc)
    pay_day = day_counts.most_common(1)[0][0]

    # Check whether recurring income was already credited in ref_date's calendar month
    inc_this_month = any(
        t.get("amount", 0) > 0
        and (t.get("is_recurring") or t.get("category") == "Income")
        and t.get("date").year == ref_date.year
        and t.get("date").month == ref_date.month
        for t in transactions
    )

    if not inc_this_month and ref_date.day <= pay_day:
        next_date = date(ref_date.year, ref_date.month, min(pay_day, 28))
        is_upcoming_this_cycle = True
    elif not inc_this_month and ref_date.day > pay_day:
        # Month started, but statement ended before credit line was captured
        next_date = ref_date
        is_upcoming_this_cycle = True
    else:
        is_upcoming_this_cycle = False
        if ref_date.month == 12:
            next_date = date(ref_date.year + 1, 1, min(pay_day, 31))
        else:
            nm = ref_date.month + 1
            max_d = 28 if nm == 2 else (30 if nm in [4, 6, 9, 11] else 31)
            next_date = date(ref_date.year, nm, min(pay_day, max_d))

    return next_date, typical_amt, is_upcoming_this_cycle


def extract_upcoming_obligations(
    transactions: List[Dict],
    calendar_events: List[Dict],
    ref_date: date,
    remaining_days: int,
) -> Tuple[List[Dict], float]:
    """
    Gathers all upcoming commitments due within the planning period [ref_date, ref_date + remaining_days).
    Includes recurring debit streams from the bank statement (Rent, EMIs, SIPs, utilities, subscriptions)
    and any scheduled calendar events.
    """
    from app.services.recurring_detector import _normalize_desc

    end_date = ref_date + timedelta(days=remaining_days)
    obligations = []
    seen = set()

    # 1. Statement recurring debit transactions
    rec_groups = defaultdict(list)
    for t in transactions:
        if t.get("amount", 0) < 0 and t.get("is_recurring"):
            key = _normalize_desc(t.get("description", "")) or t.get("description", "")
            rec_groups[key].append(t)

    for key, items in rec_groups.items():
        avg_cost = round(float(mean(-t["amount"] for t in items)), 2)
        day_counts = Counter(t["date"].day for t in items)
        typical_day = day_counts.most_common(1)[0][0]
        title = items[0].get("description") or key
        category = items[0].get("category", "Recurring")

        # Due date in ref_date's month
        due = date(ref_date.year, ref_date.month, min(typical_day, 28 if ref_date.month == 2 else 30))
        if ref_date <= due < end_date:
            obligations.append({
                "title": title,
                "date": due,
                "estimated_cost": avg_cost,
                "category": category,
                "source": "statement",
            })
            seen.add(title.lower())
        else:
            # Check next month if planning horizon extends into it
            if ref_date.month == 12:
                due_next = date(ref_date.year + 1, 1, min(typical_day, 31))
            else:
                nm = ref_date.month + 1
                max_d = 28 if nm == 2 else (30 if nm in [4, 6, 9, 11] else 31)
                due_next = date(ref_date.year, nm, min(typical_day, max_d))
            if ref_date <= due_next < end_date:
                obligations.append({
                    "title": title,
                    "date": due_next,
                    "estimated_cost": avg_cost,
                    "category": category,
                    "source": "statement",
                })
                seen.add(title.lower())

    # 2. External calendar events
    for e in (calendar_events or []):
        edate = e.get("date")
        if isinstance(edate, str):
            try:
                edate = date.fromisoformat(edate)
            except ValueError:
                continue
        if edate and ref_date <= edate < end_date:
            etitle = e.get("title", "Event")
            if etitle.lower() not in seen:
                obligations.append({
                    "title": etitle,
                    "date": edate,
                    "estimated_cost": round(float(e.get("estimated_cost", 0.0)), 2),
                    "category": e.get("category_hint", "Calendar Event"),
                    "source": "calendar",
                })
                seen.add(etitle.lower())

    obligations.sort(key=lambda o: (o["date"], o["title"]))
    total_cost = round(sum(o["estimated_cost"] for o in obligations), 2)
    return obligations, total_cost


def calculate_essential_daily_rate(transactions: List[Dict]) -> float:
    """
    Estimates baseline daily essential spend (groceries, transport, health, dining)
    excluding fixed recurring bills already handled in upcoming obligations.
    """
    debit_txns = [t for t in transactions if t.get("amount", 0) < 0]
    if not debit_txns:
        return 0.0

    ess_txns = [
        t for t in debit_txns
        if str(t.get("category", "")).lower() in ESSENTIAL_CATEGORIES and not t.get("is_recurring")
    ]
    dates = [t["date"] for t in transactions if "date" in t]
    if not dates:
        return 0.0
    span_days = max(1, (max(dates) - min(dates)).days + 1)
    total_ess = sum(-t["amount"] for t in ess_txns)
    return round(total_ess / span_days, 2)


def compute_safe_to_spend(
    transactions: List[Dict],
    upcoming_obligations: List[Dict],  # [{title, date, estimated_cost}]
    today: date,
    known_balance: float = None,
    **kwargs,
) -> Dict:
    """
    Calculates Safe-to-Spend dynamically using actual extracted statement data.
    Returns the daily allowance, period summary, and transparent breakdown.
    """
    balance = compute_current_balance(transactions, known_balance)

    # 1. Income detection & next income date
    next_income_date, typical_income, is_upcoming_this_cycle = detect_recurring_income(transactions, today)

    # 2. Determine relevant planning period
    m_left = days_left_in_month(today)
    if is_upcoming_this_cycle:
        remaining_days = max(1, m_left)
        d_str = next_income_date.strftime("%d %b") if next_income_date else "soon"
        period_label = f"{remaining_days} days in month (next income {d_str})"
        exp_inc_in_period = typical_income
    elif next_income_date and next_income_date > today:
        days_to_income = (next_income_date - today).days
        if 1 <= days_to_income <= 45:
            remaining_days = days_to_income
            d_str = next_income_date.strftime("%d %b")
            period_label = f"{remaining_days} days until next income on {d_str}"
            exp_inc_in_period = 0.0
        else:
            remaining_days = max(1, m_left)
            period_label = f"{remaining_days} days until month-end"
            exp_inc_in_period = 0.0
    else:
        remaining_days = max(1, m_left)
        period_label = f"{remaining_days} days until month-end"
        exp_inc_in_period = 0.0

    # 3. Upcoming obligations (statement recurring + calendar events)
    all_obligations, obligations_total = extract_upcoming_obligations(
        transactions, upcoming_obligations, today, remaining_days
    )

    # 4. Reserved essential expenses
    daily_ess = calculate_essential_daily_rate(transactions)
    reserved_essentials = round(daily_ess * remaining_days, 2)

    # 5. Safety buffer (5% of available balance)
    buffer = round(max(0.0, balance * SAFETY_BUFFER_RATIO), 2)

    # 6. Discretionary pool
    total_avail = round(balance + exp_inc_in_period, 2)
    commitments = round(obligations_total + reserved_essentials + buffer, 2)
    discretionary = max(0.0, round(total_avail - commitments, 2))

    # 7. Safe-to-spend daily allowance
    raw_daily = discretionary / remaining_days
    max_safe_today = max(0.0, balance - buffer)
    safe_today = round(min(raw_daily, max_safe_today) if max_safe_today > 0 else raw_daily, 2)

    # 8. Projected period-end balance
    projected_end = round(total_avail - obligations_total - reserved_essentials, 2)

    assumptions = (
        f"Planned over {remaining_days} days ({period_label}). "
        f"Reserved ₹{obligations_total:,.2f} for upcoming obligations, ₹{reserved_essentials:,.2f} for daily essentials, "
        f"and ₹{buffer:,.2f} safety buffer."
    )

    return {
        "today": today,
        "current_balance": balance,
        "available_balance": balance,
        "safe_to_spend_today": safe_today,
        "projected_end_of_month_balance": projected_end,
        "upcoming_obligations": all_obligations,
        "upcoming_obligations_total": obligations_total,
        "reserved_essential_expenses": reserved_essentials,
        "discretionary_funds": discretionary,
        "remaining_days": remaining_days,
        "next_expected_income_date": next_income_date.isoformat() if next_income_date else None,
        "expected_income_in_period": exp_inc_in_period,
        "planning_period_label": period_label,
        "assumptions": assumptions,
        "breakdown": {
            "available_balance": balance,
            "upcoming_obligations": obligations_total,
            "reserved_essential_expenses": reserved_essentials,
            "safety_buffer": buffer,
            "remaining_discretionary_funds": discretionary,
            "remaining_days": remaining_days,
            "final_safe_to_spend": safe_today,
        },
    }
