"""
CRUD endpoints for viewing / manually adding / editing transactions.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app import models, schemas
from app.services.categorizer import categorize

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=List[schemas.TransactionOut])
def list_transactions(
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
):
    q = db.query(models.Transaction)
    if category:
        q = q.filter(models.Transaction.category == category)
    if start:
        q = q.filter(models.Transaction.date >= start)
    if end:
        q = q.filter(models.Transaction.date <= end)
    return q.order_by(models.Transaction.date.desc()).all()


@router.post("", response_model=schemas.TransactionOut)
def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db)):
    txn = models.Transaction(
        date=payload.date,
        description=payload.description,
        amount=payload.amount,
        category=payload.category or categorize(payload.description),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.delete("/{txn_id}")
def delete_transaction(txn_id: int, db: Session = Depends(get_db)):
    txn = db.query(models.Transaction).get(txn_id)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    db.delete(txn)
    db.commit()
    return {"deleted": txn_id}
