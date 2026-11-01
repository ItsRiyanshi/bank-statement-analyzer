"""
SQLAlchemy ORM models for the whole app.
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Statement(Base):
    __tablename__ = "statements"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    source_type = Column(String, default="pdf")  # pdf | sms | csv
    content_hash = Column(String, index=True, nullable=True)
    opening_balance = Column(Float, nullable=True)
    closing_balance = Column(Float, nullable=True)
    transactions = relationship("Transaction", back_populates="statement")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("statements.id"), nullable=True)
    date = Column(Date, index=True)
    description = Column(String)
    amount = Column(Float)  # negative = debit/expense, positive = credit/income
    category = Column(String, default="Uncategorized")
    is_recurring = Column(Boolean, default=False)
    is_anomaly = Column(Boolean, default=False)
    raw_text = Column(String, nullable=True)

    statement = relationship("Statement", back_populates="transactions")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=True)  # Google Calendar event id
    title = Column(String)
    date = Column(Date, index=True)
    estimated_cost = Column(Float, default=0.0)
    category_hint = Column(String, default="Event")


class BudgetPlan(Base):
    __tablename__ = "budget_plans"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String)  # e.g. "2026-09"
    day = Column(Date)
    planned_amount = Column(Float)
    reason = Column(String, nullable=True)