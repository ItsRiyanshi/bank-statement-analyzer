"""
Pydantic schemas used for request/response validation.
"""
from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class TransactionOut(BaseModel):
    id: int
    date: date
    description: str
    amount: float
    category: str
    is_recurring: bool
    is_anomaly: bool

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    date: date
    description: str
    amount: float
    category: Optional[str] = None


class AnalyticsSummary(BaseModel):
    total_income: float
    total_expense: float
    net: float
    by_category: dict
    monthly_trend: List[dict]


class HealthScoreOut(BaseModel):
    score: int
    grade: str
    breakdown: dict
    tips: List[str]


class SafeToSpendOut(BaseModel):
    today: date
    safe_to_spend_today: float
    projected_end_of_month_balance: float
    upcoming_obligations: List[dict]


class CalendarEventIn(BaseModel):
    title: str
    date: date
    estimated_cost: Optional[float] = None
    category_hint: Optional[str] = "Event"


class CalendarEventOut(CalendarEventIn):
    id: int

    class Config:
        from_attributes = True


class BudgetDayOut(BaseModel):
    day: date
    planned_amount: float
    reason: Optional[str] = None
    has_event: bool = False
