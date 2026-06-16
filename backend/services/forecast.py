from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List, Dict, Any
from backend.models import Period, Scenario, ForecastRule, DriverValue, BudgetLine
from backend.services.variance import calculate_variance

def compute_forecast(db: Session, scenario_id: int, period_name: str) -> List[Dict[str, Any]]:
    period = db.query(Period).filter(Period.name == period_name).first()
    if not period:
        return []

    rules = db.query(ForecastRule).options(
        joinedload(ForecastRule.drivers),
        joinedload(ForecastRule.department),
        joinedload(ForecastRule.account)
    ).filter(ForecastRule.period_id == period.id).all()

    # Load all driver values for the scenario in one query (N+1 fix)
    driver_values_qs = db.query(DriverValue).filter(DriverValue.scenario_id == scenario_id).all()
    driver_values_map = {dv.driver_id: dv.value for dv in driver_values_qs}

    forecasts = []
    for rule in rules:
        drivers = rule.drivers
        if not drivers:
            forecast_amount = 0.0
        else:
            forecast_amount = 1.0
            for d in drivers:
                val = driver_values_map.get(d.id, 0.0)
                forecast_amount *= val

        forecasts.append({
            "department_id": rule.department.id,
            "department": rule.department.name,
            "account_id": rule.account.id,
            "account": rule.account.name,
            "account_type": rule.account.type,
            "forecast": forecast_amount
        })

    return forecasts

def forecast_vs_budget(db: Session, scenario_id: int, period_name: str) -> List[Dict[str, Any]]:
    forecasts = compute_forecast(db, scenario_id, period_name)

    period = db.query(Period).filter(Period.name == period_name).first()
    if not period:
        return []

    budget_lines = db.query(BudgetLine).filter(BudgetLine.period_id == period.id).all()
    budget_map = {(bl.department_id, bl.account_id): bl.amount for bl in budget_lines}

    results = []
    for f in forecasts:
        budget_amt = budget_map.get((f["department_id"], f["account_id"]), 0.0)
        
        # Reuse pure variance logic. Forecast acts as the "actual".
        variance, variance_pct, is_favorable = calculate_variance(
            budget=budget_amt,
            actual=f["forecast"],
            account_type=f["account_type"]
        )

        results.append({
            "department": f["department"],
            "account": f["account"],
            "account_type": f["account_type"].value if hasattr(f["account_type"], 'value') else f["account_type"],
            "budget": budget_amt,
            "forecast": f["forecast"],
            "variance": variance,
            "variance_percentage": variance_pct,
            "is_favorable": is_favorable
        })

    return results
