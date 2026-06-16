import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, Scenario, Driver, DriverValue, ForecastRule, Department, Period, Account, AccountType, BudgetLine
from backend.services.forecast import compute_forecast, forecast_vs_budget
from datetime import date

# In-memory SQLite for isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Setup base data
    dept = Department(name="Sales")
    period = Period(name="2024-01", start_date=date(2024,1,1), end_date=date(2024,1,31))
    acc_rev = Account(name="Revenue", type=AccountType.revenue)
    acc_cost = Account(name="Cost", type=AccountType.cost)
    session.add_all([dept, period, acc_rev, acc_cost])
    session.commit()

    base_scen = Scenario(name="Base", is_baseline=True)
    upside_scen = Scenario(name="Upside", is_baseline=False)
    session.add_all([base_scen, upside_scen])
    session.commit()

    drv_headcount = Driver(key="headcount", label="HC", unit="people")
    drv_salary = Driver(key="salary", label="Sal", unit="currency")
    session.add_all([drv_headcount, drv_salary])
    session.commit()

    # Rule: Sales Cost = headcount * salary
    rule_cost = ForecastRule(department_id=dept.id, account_id=acc_cost.id, period_id=period.id)
    rule_cost.drivers = [drv_headcount, drv_salary]
    session.add(rule_cost)

    # Budget for cost
    b_cost = BudgetLine(department_id=dept.id, account_id=acc_cost.id, period_id=period.id, amount=100000)
    session.add(b_cost)

    # Base values
    session.add_all([
        DriverValue(driver_id=drv_headcount.id, scenario_id=base_scen.id, value=10),
        DriverValue(driver_id=drv_salary.id, scenario_id=base_scen.id, value=10000),
        # Upside values (only change headcount to 12)
        DriverValue(driver_id=drv_headcount.id, scenario_id=upside_scen.id, value=12),
        DriverValue(driver_id=drv_salary.id, scenario_id=upside_scen.id, value=10000)
    ])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

def test_base_forecast_equals_budget(db):
    scen = db.query(Scenario).filter_by(name="Base").first()
    results = forecast_vs_budget(db, scen.id, "2024-01")
    
    assert len(results) == 1
    res = results[0]
    assert res["forecast"] == 100000.0  # 10 * 10000
    assert res["budget"] == 100000.0
    assert res["variance"] == 0.0
    assert res["is_favorable"] is True

def test_driver_modification_isolates_change(db):
    upside = db.query(Scenario).filter_by(name="Upside").first()
    results = forecast_vs_budget(db, upside.id, "2024-01")
    
    assert len(results) == 1
    res = results[0]
    # Forecast should be 12 * 10000 = 120000
    assert res["forecast"] == 120000.0
    
    # Cost over budget is UNFAVORABLE
    assert res["variance"] == 20000.0
    assert res["is_favorable"] is False

def test_revenue_sign_flip(db):
    # Setup revenue rule and budget
    dept = db.query(Department).filter_by(name="Sales").first()
    acc_rev = db.query(Account).filter_by(name="Revenue").first()
    period = db.query(Period).filter_by(name="2024-01").first()
    base_scen = db.query(Scenario).filter_by(name="Base").first()

    drv_cust = Driver(key="customers", label="Cust", unit="count")
    drv_price = Driver(key="price", label="Price", unit="currency")
    db.add_all([drv_cust, drv_price])
    db.commit()

    rule_rev = ForecastRule(department_id=dept.id, account_id=acc_rev.id, period_id=period.id)
    rule_rev.drivers = [drv_cust, drv_price]
    db.add(rule_rev)

    b_rev = BudgetLine(department_id=dept.id, account_id=acc_rev.id, period_id=period.id, amount=50000)
    db.add(b_rev)

    db.add_all([
        DriverValue(driver_id=drv_cust.id, scenario_id=base_scen.id, value=500),
        DriverValue(driver_id=drv_price.id, scenario_id=base_scen.id, value=120)  # 500 * 120 = 60000
    ])
    db.commit()

    results = forecast_vs_budget(db, base_scen.id, "2024-01")
    rev_res = [r for r in results if r["account"] == "Revenue"][0]
    
    # Forecast = 60000, Budget = 50000. Variance = 10000.
    # Revenue over budget is FAVORABLE
    assert rev_res["forecast"] == 60000.0
    assert rev_res["variance"] == 10000.0
    assert rev_res["is_favorable"] is True

def test_zero_drivers(db):
    dept = db.query(Department).filter_by(name="Sales").first()
    period = db.query(Period).filter_by(name="2024-01").first()
    base_scen = db.query(Scenario).filter_by(name="Base").first()

    # Create a new empty account to avoid collision
    acc_empty = Account(name="EmptyAccount", type=AccountType.cost)
    db.add(acc_empty)
    db.commit()

    # Rule with NO drivers
    rule_empty = ForecastRule(department_id=dept.id, account_id=acc_empty.id, period_id=period.id)
    db.add(rule_empty)
    db.commit()

    results = forecast_vs_budget(db, base_scen.id, "2024-01")
    empty_res = [r for r in results if r["account"] == "EmptyAccount"][0]
    
    # Should safely return 0 without crashing
    assert empty_res["forecast"] == 0.0
