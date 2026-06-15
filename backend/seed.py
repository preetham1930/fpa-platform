import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend import models

def seed_db():
    # Recreate tables
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # Departments
        depts = [
            models.Department(name="Engineering"),
            models.Department(name="Sales"),
            models.Department(name="Marketing"),
            models.Department(name="HR")
        ]
        db.add_all(depts)
        db.commit()
        
        # Period
        period = models.Period(name="2024-01", start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))
        db.add(period)
        db.commit()
        
        # Accounts
        acc_rev = models.Account(name="Software Subscriptions", type=models.AccountType.revenue)
        acc_salaries = models.Account(name="Salaries", type=models.AccountType.cost)
        acc_ads = models.Account(name="Ad Spend", type=models.AccountType.cost)
        db.add_all([acc_rev, acc_salaries, acc_ads])
        db.commit()
        
        # Helper to get IDs
        dept_ids = {d.name: d.id for d in db.query(models.Department).all()}
        p_id = period.id
        rev_id = acc_rev.id
        sal_id = acc_salaries.id
        ad_id = acc_ads.id
        
        # Budgets
        budgets = [
            # Engineering
            models.BudgetLine(department_id=dept_ids["Engineering"], period_id=p_id, account_id=sal_id, amount=100000),
            # Sales
            models.BudgetLine(department_id=dept_ids["Sales"], period_id=p_id, account_id=sal_id, amount=80000),
            models.BudgetLine(department_id=dept_ids["Sales"], period_id=p_id, account_id=rev_id, amount=200000),
            # Marketing
            models.BudgetLine(department_id=dept_ids["Marketing"], period_id=p_id, account_id=sal_id, amount=50000),
            models.BudgetLine(department_id=dept_ids["Marketing"], period_id=p_id, account_id=ad_id, amount=20000),
            # HR
            models.BudgetLine(department_id=dept_ids["HR"], period_id=p_id, account_id=sal_id, amount=30000)
        ]
        db.add_all(budgets)
        
        # Actuals
        actuals = [
            # Engineering (over budget on cost -> unfavorable)
            models.ActualLine(department_id=dept_ids["Engineering"], period_id=p_id, account_id=sal_id, amount=105000),
            # Sales (under budget on cost -> favorable, over budget on revenue -> favorable)
            models.ActualLine(department_id=dept_ids["Sales"], period_id=p_id, account_id=sal_id, amount=78000),
            models.ActualLine(department_id=dept_ids["Sales"], period_id=p_id, account_id=rev_id, amount=210000),
            # Marketing (on budget for salaries, over budget on ads -> unfavorable)
            models.ActualLine(department_id=dept_ids["Marketing"], period_id=p_id, account_id=sal_id, amount=50000),
            models.ActualLine(department_id=dept_ids["Marketing"], period_id=p_id, account_id=ad_id, amount=25000),
            # HR (under budget -> favorable)
            models.ActualLine(department_id=dept_ids["HR"], period_id=p_id, account_id=sal_id, amount=29000)
        ]
        db.add_all(actuals)
        
        db.commit()
        print("Database seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
