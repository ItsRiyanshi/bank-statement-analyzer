"""
Calendar endpoints: manually add events with an estimated cost, or sync
from Google Calendar (free tier), and get the "Safe-to-Spend" number.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Optional

from app.database import get_db
from app import models, schemas
from app.services.safe_to_spend import compute_safe_to_spend
from app.services import google_calendar

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

# Rough per-category cost estimates used when a manually/Google-synced
# event doesn't have an explicit cost -- based on historical averages
# for similar categories; tune these to your own spending.
DEFAULT_EVENT_COST_ESTIMATES = {
    "birthday": 1500,
    "wedding": 5000,
    "trip": 8000,
    "dinner": 1200,
    "party": 2000,
}


def _estimate_cost(title: str) -> float:
    text = title.lower()
    for keyword, cost in DEFAULT_EVENT_COST_ESTIMATES.items():
        if keyword in text:
            return cost
    return 800  # generic fallback estimate


@router.get("/events", response_model=List[schemas.CalendarEventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(models.CalendarEvent).order_by(models.CalendarEvent.date).all()


@router.post("/events", response_model=schemas.CalendarEventOut)
def add_event(payload: schemas.CalendarEventIn, db: Session = Depends(get_db)):
    event = models.CalendarEvent(
        title=payload.title,
        date=payload.date,
        estimated_cost=payload.estimated_cost or _estimate_cost(payload.title),
        category_hint=payload.category_hint or "Event",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.CalendarEvent).get(event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    db.delete(event)
    db.commit()
    return {"deleted": event_id}


@router.post("/sync-google")
def sync_google_calendar(db: Session = Depends(get_db)):
    """Pulls events from the user's primary Google Calendar (free tier)
    and inserts any not already present."""
    try:
        events = google_calendar.fetch_upcoming_events()
    except FileNotFoundError as e:
        raise HTTPException(400, str(e))

    existing_ext_ids = {e.external_id for e in db.query(models.CalendarEvent).all() if e.external_id}
    added = 0
    for e in events:
        if e["external_id"] in existing_ext_ids:
            continue
        db.add(
            models.CalendarEvent(
                external_id=e["external_id"],
                title=e["title"],
                date=e["date"],
                estimated_cost=_estimate_cost(e["title"]),
                category_hint="Event",
            )
        )
        added += 1
    db.commit()
    return {"synced": len(events), "added": added}


@router.get("/safe-to-spend")
def safe_to_spend(db: Session = Depends(get_db), today: Optional[date] = None):
    # 1. Fetch latest uploaded statement
    latest_statement = (
        db.query(models.Statement)
        .order_by(models.Statement.uploaded_at.desc(), models.Statement.id.desc())
        .first()
    )
    if not latest_statement or not latest_statement.transactions:
        # Fallback to statement with latest transaction date
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

    # 3. Gather transactions (use latest statement's transactions if available, else full DB)
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
            "is_anomaly": t.is_anomaly,
        }
        for t in stmt_txns
    ]

    # 4. Determine anchor date
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
        {"title": e.title, "date": e.date, "estimated_cost": e.estimated_cost, "category_hint": e.category_hint}
        for e in db.query(models.CalendarEvent).all()
    ]

    return compute_safe_to_spend(txns, events, today, known_balance=known_balance)