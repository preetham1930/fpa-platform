from datetime import date
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, Date, Enum, ForeignKey
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
