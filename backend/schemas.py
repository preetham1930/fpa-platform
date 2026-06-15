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
