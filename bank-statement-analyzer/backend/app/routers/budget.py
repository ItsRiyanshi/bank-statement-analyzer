"""
Adaptive rest-of-month budget planner endpoint. Combines transaction
history + calendar events to output a per-day spending plan for the
remainder of the current month.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional

from app.database import get_db
from app import models
from app.services.budget_planner import plan_rest_of_month

router = APIRouter(prefix="/api/budget", tags=["budget"])


@router.get("/plan")
def get_budget_plan(db: Session = Depends(get_db), today: Optional[date] = None):
    # 1. Fetch latest uploaded statement
    latest_statement = (
        db.query(models.Statement)
        .order_by(models.Statement.uploaded_at.desc(), models.Statement.id.desc())
        .first()
    )
    if not latest_statement or not latest_statement.transactions:
        latest_statement = (
            db.query(models.Statement)
            .join(models.Transaction)
            .group_by(models.Statement.id)
            .order_by(func.max(models.Transaction.date).desc())
            .first()
        )

    # 2. Extract true available balance
    known_balance = None
    if latest_statement:
        if latest_statement.closing_balance is not None:
            known_balance = float(latest_statement.closing_balance)
        elif latest_statement.opening_balance is not None and latest_statement.transactions:
            net_delta = sum(t.amount for t in latest_statement.transactions)
            known_balance = round(float(latest_statement.opening_balance + net_delta), 2)
        elif latest_statement.transactions:
            known_balance = round(float(sum(t.amount for t in latest_statement.transactions)), 2)

    all_db_txns = db.query(models.Transaction).all()
    stmt_txns = latest_statement.transactions if (latest_statement and latest_statement.transactions) else all_db_txns

    if known_balance is None:
        known_balance = round(float(sum(t.amount for t in all_db_txns)), 2) if all_db_txns else 0.0

    txns = [
        {
            "id": t.id,
            "date": t.date,
            "amount": t.amount,
            "category": t.category,
            "description": t.description,
            "is_recurring": t.is_recurring,
        }
        for t in stmt_txns
    ]

    # 3. Determine anchor date
    if today is None:
        latest_txn_date = max((t["date"] for t in txns), default=None)
        today_cand = date.today()
        if latest_txn_date:
            if abs((today_cand - latest_txn_date).days) <= 35:
                today = today_cand
            else:
                today = latest_txn_date
        else:
            today = today_cand

    events = [
        {"date": e.date, "title": e.title, "estimated_cost": e.estimated_cost}
        for e in db.query(models.CalendarEvent).filter(models.CalendarEvent.date >= today).all()
    ]

    plan = plan_rest_of_month(txns, events, today, known_balance=known_balance)
    return plan