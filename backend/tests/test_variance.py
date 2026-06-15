from backend.services.variance import calculate_variance
from backend.models import AccountType
import pytest

def test_revenue_favorable():
    variance, pct, is_favorable = calculate_variance(budget=100.0, actual=120.0, account_type=AccountType.revenue)
    assert variance == 20.0
    assert pct == 20.0
    assert is_favorable is True

def test_revenue_unfavorable():
    variance, pct, is_favorable = calculate_variance(budget=100.0, actual=80.0, account_type=AccountType.revenue)
    assert variance == -20.0
    assert pct == -20.0
    assert is_favorable is False

def test_cost_favorable():
    variance, pct, is_favorable = calculate_variance(budget=100.0, actual=80.0, account_type=AccountType.cost)
    assert variance == -20.0
    assert pct == -20.0
    assert is_favorable is True

def test_cost_unfavorable():
    variance, pct, is_favorable = calculate_variance(budget=100.0, actual=120.0, account_type=AccountType.cost)
    assert variance == 20.0
    assert pct == 20.0
    assert is_favorable is False

def test_budget_zero():
    variance, pct, is_favorable = calculate_variance(budget=0.0, actual=50.0, account_type=AccountType.revenue)
    assert variance == 50.0
    assert pct is None
    assert is_favorable is True

def test_actual_equals_budget():
    # Revenue
    variance, pct, is_favorable = calculate_variance(budget=100.0, actual=100.0, account_type=AccountType.revenue)
    assert variance == 0.0
    assert pct == 0.0
    assert is_favorable is True

    # Cost
    variance, pct, is_favorable = calculate_variance(budget=100.0, actual=100.0, account_type=AccountType.cost)
    assert variance == 0.0
    assert pct == 0.0
    assert is_favorable is True
