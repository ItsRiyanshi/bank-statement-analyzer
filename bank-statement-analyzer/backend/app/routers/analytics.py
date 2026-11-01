"""
Analytics endpoints: category breakdown, monthly trend, financial health
score, and the plain-English monthly summary.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import defaultdict

from app.database import get_db
from app import models
from app.services.health_score import compute_health_score
from app.services.summarizer import generate_monthly_summary

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _txn_to_dict(t: models.Transaction) -> dict:
    return {
        "date": t.date,
        "description": t.description,
        "amount": t.amount,
        "category": t.category,
        "is_recurring": t.is_recurring,
        "is_anomaly": t.is_anomaly,
    }


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    txns = db.query(models.Transaction).all()
    income = sum(t.amount for t in txns if t.amount > 0)
    expense = sum(-t.amount for t in txns if t.amount < 0)

    by_category = defaultdict(float)
    for t in txns:
        if t.amount < 0:
            by_category[t.category] += -t.amount

    monthly = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for t in txns:
        key = t.date.strftime("%Y-%m")
        if t.amount > 0:
            monthly[key]["income"] += t.amount
        else:
            monthly[key]["expense"] += -t.amount
    monthly_trend = [{"month": k, **v} for k, v in sorted(monthly.items())]

    return {
        "total_income": round(income, 2),
        "total_expense": round(expense, 2),
        "net": round(income - expense, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "monthly_trend": monthly_trend,
    }


@router.get("/health-score")
def get_health_score(db: Session = Depends(get_db)):
    txns = [_txn_to_dict(t) for t in db.query(models.Transaction).all()]
    return compute_health_score(txns)


@router.get("/recurring")
def get_recurring(db: Session = Depends(get_db)):
    txns = db.query(models.Transaction).filter(models.Transaction.is_recurring == True).all()
    return [_txn_to_dict(t) for t in txns]


@router.get("/anomalies")
def get_anomalies(db: Session = Depends(get_db)):
    txns = db.query(models.Transaction).filter(models.Transaction.is_anomaly == True).all()
    return [_txn_to_dict(t) for t in txns]


@router.get("/summary-text")
def get_summary_text(db: Session = Depends(get_db)):
    txns = [_txn_to_dict(t) for t in db.query(models.Transaction).all()]
    analytics_resp = get_summary(db)
    health = compute_health_score(txns)
    return {"summary": generate_monthly_summary(analytics_resp, health)}


@router.get("/safe-to-spend")
def get_analytics_safe_to_spend(db: Session = Depends(get_db)):
    from app.routers.calendar import safe_to_spend
    return safe_to_spend(db=db)
