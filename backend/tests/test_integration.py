import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json
from datetime import date

from backend.database import Base
from backend.models import Department, Account, Period, AccountType, ExternalMapping, ActualLine, SyncRun
from backend.services.integration import sync_actuals

# Setup in-memory DB for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # 1. Setup Period
    period = Period(name="2026-05", start_date=date(2026, 5, 1), end_date=date(2026, 5, 31))
    session.add(period)
    
    # 2. Setup Departments
    dept_eng = Department(name="Engineering")
    dept_sales = Department(name="Sales")
    dept_mkt = Department(name="Marketing")
    dept_hr = Department(name="HR")
    session.add_all([dept_eng, dept_sales, dept_mkt, dept_hr])
    
    # 3. Setup Accounts
    acc_sal = Account(name="Salaries", type=AccountType.cost)
    acc_rev = Account(name="Software Subscriptions", type=AccountType.revenue)
    acc_ad = Account(name="Ad Spend", type=AccountType.cost)
    session.add_all([acc_sal, acc_rev, acc_ad])
    session.commit()

    # 4. Setup External Mappings
    mappings = [
        ExternalMapping(source="SAP", entity_type="department", external_code="CC-ENG", internal_id=dept_eng.id),
        ExternalMapping(source="SAP", entity_type="department", external_code="CC-SALES", internal_id=dept_sales.id),
        ExternalMapping(source="SAP", entity_type="department", external_code="CC-MKT", internal_id=dept_mkt.id),
        ExternalMapping(source="SAP", entity_type="department", external_code="CC-HR", internal_id=dept_hr.id),
        ExternalMapping(source="SAP", entity_type="account", external_code="GL-SAL", internal_id=acc_sal.id),
        ExternalMapping(source="SAP", entity_type="account", external_code="GL-REV", internal_id=acc_rev.id),
        ExternalMapping(source="SAP", entity_type="account", external_code="GL-AD", internal_id=acc_ad.id),
    ]
    session.add_all(mappings)
    session.commit()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_sync_actuals(db):
    # 1. Run sync
    run = sync_actuals(db, "2026-05")
    
    # Check SyncRun
    assert run.status == "partial" # Expect partial due to mock unmapped/malformed records
    assert run.records_fetched == 8
    assert run.records_synced == 6
    assert run.records_rejected == 2
    
    error_detail = json.loads(run.error_detail)
    assert len(error_detail) == 2
    
    # Verify ActualLines inserted
    actuals = db.query(ActualLine).all()
    assert len(actuals) == 6
    for a in actuals:
        assert a.source == "SAP"

def test_sync_actuals_idempotency(db):
    # Run first sync
    sync_actuals(db, "2026-05")
    
    # Run second sync
    run = sync_actuals(db, "2026-05")
    
    assert run.records_fetched == 8
    assert run.records_synced == 6
    assert run.records_rejected == 2
    
    # Verify ActualLines count hasn't doubled
    actuals = db.query(ActualLine).all()
    assert len(actuals) == 6

def test_sync_actuals_invalid_period(db):
    run = sync_actuals(db, "2099-01")
    assert run.status == "failed"
    error_detail = json.loads(run.error_detail)
    assert "not found" in error_detail[0]["error"]
