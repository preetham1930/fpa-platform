from datetime import date
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, Date, Enum, ForeignKey, Boolean, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base

class AccountType(str, PyEnum):
    revenue = "revenue"
    cost = "cost"

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    budget_lines = relationship("BudgetLine", back_populates="department")
    actual_lines = relationship("ActualLine", back_populates="department")

class Period(Base):
    __tablename__ = "periods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # e.g., "2024-01"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    budget_lines = relationship("BudgetLine", back_populates="period")
    actual_lines = relationship("ActualLine", back_populates="period")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    type = Column(Enum(AccountType), nullable=False)

    budget_lines = relationship("BudgetLine", back_populates="account")
    actual_lines = relationship("ActualLine", back_populates="account")

class BudgetLine(Base):
    __tablename__ = "budget_lines"
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)

    department = relationship("Department", back_populates="budget_lines")
    period = relationship("Period", back_populates="budget_lines")
    account = relationship("Account", back_populates="budget_lines")

class ActualLine(Base):
    __tablename__ = "actual_lines"
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)

    department = relationship("Department", back_populates="actual_lines")
    period = relationship("Period", back_populates="actual_lines")
    account = relationship("Account", back_populates="actual_lines")

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, nullable=False)
    unit = Column(String, nullable=False)

class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    is_baseline = Column(Boolean, default=False, nullable=False)

class DriverValue(Base):
    __tablename__ = "driver_values"
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    value = Column(Float, nullable=False)
    
    __table_args__ = (UniqueConstraint("driver_id", "scenario_id", name="_driver_scenario_uc"),)

    driver = relationship("Driver")
    scenario = relationship("Scenario")

class ForecastRule(Base):
    __tablename__ = "forecast_rules"
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False)

    department = relationship("Department")
    account = relationship("Account")
    period = relationship("Period")
    
rule_driver_association = Table(
    "rule_driver_association",
    Base.metadata,
    Column("rule_id", Integer, ForeignKey("forecast_rules.id")),
    Column("driver_id", Integer, ForeignKey("drivers.id"))
)

ForecastRule.drivers = relationship("Driver", secondary=rule_driver_association)
