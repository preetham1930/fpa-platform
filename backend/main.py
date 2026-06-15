from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from typing import List

from backend import models, schemas
from backend.database import engine, get_db
from backend.services.variance import calculate_variance

# Create database tables for Phase 1 locally
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FP&A Platform API")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For public read-only demo
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/budgets", response_model=schemas.BudgetLineOut)
def create_budget(budget: schemas.BudgetLineCreate, db: Session = Depends(get_db)):
    db_budget = models.BudgetLine(**budget.model_dump())
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@app.post("/actuals", response_model=schemas.ActualLineOut)
def create_actual(actual: schemas.ActualLineCreate, db: Session = Depends(get_db)):
    db_actual = models.ActualLine(**actual.model_dump())
    db.add(db_actual)
    db.commit()
    db.refresh(db_actual)
    return db_actual

@app.get("/variance", response_model=schemas.VarianceReport)
def get_variance_report(period: int, db: Session = Depends(get_db)):
    # Verify period exists
    db_period = db.query(models.Period).filter(models.Period.id == period).first()
    if not db_period:
        raise HTTPException(status_code=404, detail="Period not found")
        
    budgets = db.query(models.BudgetLine).filter(models.BudgetLine.period_id == period).all()
    actuals = db.query(models.ActualLine).filter(models.ActualLine.period_id == period).all()
    
    # Pre-fetch for names
    departments = {d.id: d.name for d in db.query(models.Department).all()}
    accounts = {a.id: a for a in db.query(models.Account).all()}
    
    # Group by (department_id, account_id)
    summary = {}
    for b in budgets:
        key = (b.department_id, b.account_id)
        if key not in summary:
            summary[key] = {"budget": 0.0, "actual": 0.0}
        summary[key]["budget"] += b.amount
        
    for a in actuals:
        key = (a.department_id, a.account_id)
        if key not in summary:
            summary[key] = {"budget": 0.0, "actual": 0.0}
        summary[key]["actual"] += a.amount
        
    items = []
    for (dept_id, acc_id), data in summary.items():
        account = accounts.get(acc_id)
        if not account:
            continue
            
        variance, pct, is_favorable = calculate_variance(
            budget=data["budget"],
            actual=data["actual"],
            account_type=account.type
        )
        
        items.append(schemas.VarianceItem(
            department=departments.get(dept_id, "Unknown"),
            account=account.name,
            account_type=account.type,
            budget=data["budget"],
            actual=data["actual"],
            variance=variance,
            variance_percentage=pct,
            is_favorable=is_favorable
        ))
        
    # Sort items by department name then account name
    items.sort(key=lambda x: (x.department, x.account))
        
    return schemas.VarianceReport(period=db_period.name, items=items)
