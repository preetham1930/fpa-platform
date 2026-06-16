from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from backend.models import AccountType

class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentOut(DepartmentBase):
    id: int

    class Config:
        from_attributes = True

class PeriodBase(BaseModel):
    name: str
    start_date: date
    end_date: date

class PeriodCreate(PeriodBase):
    pass

class PeriodOut(PeriodBase):
    id: int

    class Config:
        from_attributes = True

class AccountBase(BaseModel):
    name: str
    type: AccountType

class AccountCreate(AccountBase):
    pass

class AccountOut(AccountBase):
    id: int

    class Config:
        from_attributes = True

class BudgetLineBase(BaseModel):
    department_id: int
    period_id: int
    account_id: int
    amount: float

class BudgetLineCreate(BudgetLineBase):
    pass

class BudgetLineOut(BudgetLineBase):
    id: int

    class Config:
        from_attributes = True

class ActualLineBase(BaseModel):
    department_id: int
    period_id: int
    account_id: int
    amount: float

class ActualLineCreate(ActualLineBase):
    pass

class ActualLineOut(ActualLineBase):
    id: int

    class Config:
        from_attributes = True

# Variance Report Schemas
class VarianceItem(BaseModel):
    department: str
    account: str
    account_type: AccountType
    budget: float
    actual: float
    variance: float
    variance_percentage: Optional[float]
    is_favorable: bool

class VarianceReport(BaseModel):
    period: str
    items: List[VarianceItem]

# Forecasting Schemas
class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioOut(ScenarioBase):
    id: int
    is_baseline: bool

    class Config:
        from_attributes = True

class DriverOut(BaseModel):
    id: int
    key: str
    label: str
    unit: str

    class Config:
        from_attributes = True

class DriverValueUpdate(BaseModel):
    value: float

class DriverValueOut(BaseModel):
    id: int
    driver_id: int
    scenario_id: int
    value: float
    driver: DriverOut

    class Config:
        from_attributes = True

class ForecastItem(BaseModel):
    department: str
    account: str
    account_type: AccountType
    budget: float
    forecast: float
    variance: float
    variance_percentage: Optional[float]
    is_favorable: bool

class ForecastReport(BaseModel):
    scenario_id: int
    period: str
    items: List[ForecastItem]

class CompareScenarioResult(BaseModel):
    forecast: float
    variance: float
    variance_percentage: Optional[float]
    is_favorable: bool

class CompareItem(BaseModel):
    department: str
    account: str
    account_type: AccountType
    budget: float
    scenarios: dict[int, CompareScenarioResult]

class CompareReport(BaseModel):
    period: str
    items: List[CompareItem]

# Integration Schemas
class SyncRunBase(BaseModel):
    source: str
    period: str

from datetime import date, datetime

class SyncRunOut(SyncRunBase):
    id: int
    status: str
    records_fetched: int
    records_synced: int
    records_rejected: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_detail: Optional[str] = None

    class Config:
        from_attributes = True

class SyncRunDetail(SyncRunOut):
    error_detail: Optional[str] = None
