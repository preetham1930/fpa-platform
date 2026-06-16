import json
from abc import ABC, abstractmethod
from typing import TypedDict, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.models import SyncRun, ExternalMapping, ActualLine, Period

class SAPRecord(TypedDict):
    cost_center: str
    gl_account: str
    amount: float
    period: str

class ERPConnector(ABC):
    @abstractmethod
    def fetch_actuals(self, period: str) -> List[SAPRecord]:
        pass

class MockSAPConnector(ERPConnector):
    def fetch_actuals(self, period: str) -> List[SAPRecord]:
        return [
            # Valid ones matching seed:
            {"cost_center": "CC-ENG", "gl_account": "GL-SAL", "amount": 105000, "period": period},
            {"cost_center": "CC-SALES", "gl_account": "GL-SAL", "amount": 78000, "period": period},
            {"cost_center": "CC-SALES", "gl_account": "GL-REV", "amount": 210000, "period": period},
            {"cost_center": "CC-MKT", "gl_account": "GL-SAL", "amount": 50000, "period": period},
            {"cost_center": "CC-MKT", "gl_account": "GL-AD", "amount": 25000, "period": period},
            {"cost_center": "CC-HR", "gl_account": "GL-SAL", "amount": 29000, "period": period},
            # Invalid mapping
            {"cost_center": "CC-UNKNOWN", "gl_account": "GL-SAL", "amount": 10000, "period": period},
            # Malformed amount
            {"cost_center": "CC-ENG", "gl_account": "GL-SAL", "amount": "INVALID", "period": period}, # type: ignore
        ]

def sync_actuals(db: Session, period_name: str, source: str = "SAP") -> SyncRun:
    run = SyncRun(
        source=source,
        period=period_name,
        status="running",
        started_at=datetime.now(timezone.utc)
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # 1. Resolve Period
    period_obj = db.query(Period).filter(Period.name == period_name).first()
    if not period_obj:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_detail = json.dumps([{"error": f"Period '{period_name}' not found."}])
        db.commit()
        db.refresh(run)
        return run

    # 2. Fetch external mappings
    dept_mappings = {
        m.external_code: m.internal_id 
        for m in db.query(ExternalMapping).filter_by(source=source, entity_type="department").all()
    }
    acc_mappings = {
        m.external_code: m.internal_id 
        for m in db.query(ExternalMapping).filter_by(source=source, entity_type="account").all()
    }

    # 3. Fetch records
    connector = MockSAPConnector() # Hardcoded dependency for this phase
    try:
        raw_records = connector.fetch_actuals(period_name)
    except Exception as e:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_detail = json.dumps([{"error": f"Connector fetch failed: {str(e)}"}])
        db.commit()
        db.refresh(run)
        return run

    run.records_fetched = len(raw_records)
    rejected_records = []
    synced_count = 0

    # 4. Process each record
    for record in raw_records:
        cost_center = record.get("cost_center")
        gl_account = record.get("gl_account")
        raw_amount = record.get("amount")

        # Validate amount
        try:
            if raw_amount is None:
                raise ValueError("Amount is None")
            amount = float(raw_amount)
        except (ValueError, TypeError):
            rejected_records.append({"record": record, "reason": "Invalid or missing amount"})
            continue

        # Map to internal IDs
        dept_id = dept_mappings.get(cost_center)
        acc_id = acc_mappings.get(gl_account)

        if not dept_id:
            rejected_records.append({"record": record, "reason": f"Unknown cost_center: {cost_center}"})
            continue
        
        if not acc_id:
            rejected_records.append({"record": record, "reason": f"Unknown gl_account: {gl_account}"})
            continue

        # Upsert ActualLine
        line = db.query(ActualLine).filter_by(
            department_id=dept_id,
            account_id=acc_id,
            period_id=period_obj.id
        ).first()

        if line:
            line.amount = amount
            line.source = source
        else:
            line = ActualLine(
                department_id=dept_id,
                account_id=acc_id,
                period_id=period_obj.id,
                amount=amount,
                source=source
            )
            db.add(line)
        
        synced_count += 1

    run.records_synced = synced_count
    run.records_rejected = len(rejected_records)
    run.finished_at = datetime.now(timezone.utc)
    
    if rejected_records:
        run.status = "partial" if synced_count > 0 else "failed"
        run.error_detail = json.dumps(rejected_records)
    else:
        run.status = "success"

    db.commit()
    db.refresh(run)
    return run
