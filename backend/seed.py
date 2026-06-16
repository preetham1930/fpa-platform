import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend import models

def seed_db():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # Phase 1 Data (Departments, Period, Accounts, Budgets, Actuals)
        depts = [
            models.Department(name="Engineering"),
            models.Department(name="Sales"),
            models.Department(name="Marketing"),
            models.Department(name="HR")
        ]
        db.add_all(depts)
        db.commit()
        
        period = models.Period(name="2026-05", start_date=date(2026, 5, 1), end_date=date(2026, 5, 31))
        db.add(period)
        db.commit()
        
        acc_rev = models.Account(name="Software Subscriptions", type=models.AccountType.revenue)
        acc_salaries = models.Account(name="Salaries", type=models.AccountType.cost)
        acc_ads = models.Account(name="Ad Spend", type=models.AccountType.cost)
        db.add_all([acc_rev, acc_salaries, acc_ads])
        db.commit()
        
        dept_ids = {d.name: d.id for d in db.query(models.Department).all()}
        p_id = period.id
        rev_id = acc_rev.id
        sal_id = acc_salaries.id
        ad_id = acc_ads.id
        
        budgets = [
            models.BudgetLine(department_id=dept_ids["Engineering"], period_id=p_id, account_id=sal_id, amount=100000),
            models.BudgetLine(department_id=dept_ids["Sales"], period_id=p_id, account_id=sal_id, amount=80000),
            models.BudgetLine(department_id=dept_ids["Sales"], period_id=p_id, account_id=rev_id, amount=200000),
            models.BudgetLine(department_id=dept_ids["Marketing"], period_id=p_id, account_id=sal_id, amount=50000),
            models.BudgetLine(department_id=dept_ids["Marketing"], period_id=p_id, account_id=ad_id, amount=20000),
            models.BudgetLine(department_id=dept_ids["HR"], period_id=p_id, account_id=sal_id, amount=30000)
        ]
        db.add_all(budgets)
        
        actuals = [
            models.ActualLine(department_id=dept_ids["Engineering"], period_id=p_id, account_id=sal_id, amount=105000),
            models.ActualLine(department_id=dept_ids["Sales"], period_id=p_id, account_id=sal_id, amount=78000),
            models.ActualLine(department_id=dept_ids["Sales"], period_id=p_id, account_id=rev_id, amount=210000),
            models.ActualLine(department_id=dept_ids["Marketing"], period_id=p_id, account_id=sal_id, amount=50000),
            models.ActualLine(department_id=dept_ids["Marketing"], period_id=p_id, account_id=ad_id, amount=25000),
            models.ActualLine(department_id=dept_ids["HR"], period_id=p_id, account_id=sal_id, amount=29000)
        ]
        db.add_all(actuals)
        db.commit()

        # Phase 2 Data
        scen_base = models.Scenario(name="Base", description="Baseline Budget", is_baseline=True)
        scen_upside = models.Scenario(name="Upside", description="Upside Scenario", is_baseline=False)
        scen_downside = models.Scenario(name="Downside", description="Downside Scenario", is_baseline=False)
        db.add_all([scen_base, scen_upside, scen_downside])
        db.commit()

        drivers_data = [
            ("eng_headcount", "Engineering Headcount", "people"),
            ("eng_avg_salary", "Engineering Avg Salary", "currency"),
            ("hr_headcount", "HR Headcount", "people"),
            ("hr_avg_salary", "HR Avg Salary", "currency"),
            ("mkt_leads", "Marketing Leads", "count"),
            ("cost_per_lead", "Cost Per Lead", "currency"),
            ("mkt_headcount", "Marketing Headcount", "people"),
            ("mkt_avg_salary", "Marketing Avg Salary", "currency"),
            ("sales_headcount", "Sales Headcount", "people"),
            ("sales_avg_salary", "Sales Avg Salary", "currency"),
            ("sales_customers", "Sales Customers", "count"),
            ("price_per_sub", "Price Per Subscription", "currency"),
        ]
        drivers = {}
        for key, label, unit in drivers_data:
            d = models.Driver(key=key, label=label, unit=unit)
            db.add(d)
            drivers[key] = d
        db.commit()

        # Base driver values
        base_values = {
            "eng_headcount": 10, "eng_avg_salary": 10000,
            "hr_headcount": 3, "hr_avg_salary": 10000,
            "mkt_leads": 400, "cost_per_lead": 50,
            "mkt_headcount": 5, "mkt_avg_salary": 10000,
            "sales_headcount": 8, "sales_avg_salary": 10000,
            "sales_customers": 1000, "price_per_sub": 200,
        }

        # Create driver values for all 3 scenarios
        for scen_id, overrides in [
            (scen_base.id, {}),
            (scen_upside.id, {"sales_customers": 1200}),
            (scen_downside.id, {"cost_per_lead": 70, "sales_customers": 900})
        ]:
            for key, base_val in base_values.items():
                val = overrides.get(key, base_val)
                db.add(models.DriverValue(driver_id=drivers[key].id, scenario_id=scen_id, value=val))
        db.commit()

        # Forecast Rules
        rules_data = [
            (dept_ids["Engineering"], sal_id, ["eng_headcount", "eng_avg_salary"]),
            (dept_ids["HR"], sal_id, ["hr_headcount", "hr_avg_salary"]),
            (dept_ids["Marketing"], ad_id, ["mkt_leads", "cost_per_lead"]),
            (dept_ids["Marketing"], sal_id, ["mkt_headcount", "mkt_avg_salary"]),
            (dept_ids["Sales"], sal_id, ["sales_headcount", "sales_avg_salary"]),
            (dept_ids["Sales"], rev_id, ["sales_customers", "price_per_sub"])
        ]
        
        for dept, acc, driver_keys in rules_data:
            rule = models.ForecastRule(department_id=dept, account_id=acc, period_id=p_id)
            rule.drivers = [drivers[k] for k in driver_keys]
            db.add(rule)
        db.commit()

        # Phase 3a Data (External Mappings)
        mappings = [
            models.ExternalMapping(source="SAP", entity_type="department", external_code="CC-ENG", internal_id=dept_ids["Engineering"]),
            models.ExternalMapping(source="SAP", entity_type="department", external_code="CC-SALES", internal_id=dept_ids["Sales"]),
            models.ExternalMapping(source="SAP", entity_type="department", external_code="CC-MKT", internal_id=dept_ids["Marketing"]),
            models.ExternalMapping(source="SAP", entity_type="department", external_code="CC-HR", internal_id=dept_ids["HR"]),
            models.ExternalMapping(source="SAP", entity_type="account", external_code="GL-SAL", internal_id=sal_id),
            models.ExternalMapping(source="SAP", entity_type="account", external_code="GL-REV", internal_id=rev_id),
            models.ExternalMapping(source="SAP", entity_type="account", external_code="GL-AD", internal_id=ad_id),
        ]
        db.add_all(mappings)
        db.commit()

        print("Database seeded successfully with Phase 2 and 3a data!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
