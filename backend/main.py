from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from typing import List

from backend import models, schemas
from backend.database import engine, get_db
from backend.services.variance import calculate_variance
from backend.services.forecast import compute_forecast, forecast_vs_budget

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
def get_variance_report(period: str, db: Session = Depends(get_db)):
    # Verify period exists
    db_period = db.query(models.Period).filter(models.Period.name == period).first()
    if not db_period:
        raise HTTPException(status_code=404, detail="Period not found")
        
    budgets = db.query(models.BudgetLine).filter(models.BudgetLine.period_id == db_period.id).all()
    actuals = db.query(models.ActualLine).filter(models.ActualLine.period_id == db_period.id).all()
    
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

# --- Phase 2 Endpoints ---

@app.get("/scenarios", response_model=List[schemas.ScenarioOut])
def get_scenarios(db: Session = Depends(get_db)):
    return db.query(models.Scenario).all()

@app.post("/scenarios", response_model=schemas.ScenarioOut)
def create_scenario(scenario: schemas.ScenarioCreate, db: Session = Depends(get_db)):
    baseline = db.query(models.Scenario).filter(models.Scenario.is_baseline == True).first()
    if not baseline:
        raise HTTPException(status_code=400, detail="Baseline scenario not found. Cannot clone.")
    
    new_scenario = models.Scenario(
        name=scenario.name,
        description=scenario.description,
        is_baseline=False
    )
    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)

    # Clone driver values from baseline
    baseline_values = db.query(models.DriverValue).filter(models.DriverValue.scenario_id == baseline.id).all()
    for dv in baseline_values:
        new_dv = models.DriverValue(
            driver_id=dv.driver_id,
            scenario_id=new_scenario.id,
            value=dv.value
        )
        db.add(new_dv)
    db.commit()
    return new_scenario

@app.get("/drivers", response_model=List[schemas.DriverOut])
def get_drivers(db: Session = Depends(get_db)):
    return db.query(models.Driver).all()

@app.get("/scenarios/{scenario_id}/drivers", response_model=List[schemas.DriverValueOut])
def get_scenario_drivers(scenario_id: int, db: Session = Depends(get_db)):
    return db.query(models.DriverValue).filter(models.DriverValue.scenario_id == scenario_id).order_by(models.DriverValue.driver_id).all()

@app.put("/scenarios/{scenario_id}/drivers/{driver_id}", response_model=schemas.DriverValueOut)
def update_driver_value(scenario_id: int, driver_id: int, data: schemas.DriverValueUpdate, db: Session = Depends(get_db)):
    dv = db.query(models.DriverValue).filter(
        models.DriverValue.scenario_id == scenario_id,
        models.DriverValue.driver_id == driver_id
    ).first()
    if not dv:
        raise HTTPException(status_code=404, detail="Driver value not found")
    dv.value = data.value
    db.commit()
    db.refresh(dv)
    return dv

@app.get("/forecast", response_model=schemas.ForecastReport)
def get_forecast(scenario: int, period: str, db: Session = Depends(get_db)):
    results = forecast_vs_budget(db, scenario, period)
    return schemas.ForecastReport(scenario_id=scenario, period=period, items=results)

@app.get("/forecast/compare", response_model=schemas.CompareReport)
def compare_forecasts(scenarios: str, period: str, db: Session = Depends(get_db)):
    scenario_ids = [int(s) for s in scenarios.split(",") if s.strip().isdigit()]
    
    all_results = {}
    for sid in scenario_ids:
        all_results[sid] = forecast_vs_budget(db, sid, period)
        
    pivoted = {}
    for sid, items in all_results.items():
        for item in items:
            key = (item["department"], item["account"], item["account_type"], item["budget"])
            if key not in pivoted:
                pivoted[key] = {}
            pivoted[key][sid] = {
                "forecast": item["forecast"],
                "variance": item["variance"],
                "variance_percentage": item["variance_percentage"],
                "is_favorable": item["is_favorable"]
            }
            
    compare_items = []
    for (dept, acc, acc_type, budget), scenario_dict in pivoted.items():
        compare_items.append(schemas.CompareItem(
            department=dept,
            account=acc,
            account_type=acc_type,
            budget=budget,
            scenarios=scenario_dict
        ))
        
    compare_items.sort(key=lambda x: (x.department, x.account))
    return schemas.CompareReport(period=period, items=compare_items)
