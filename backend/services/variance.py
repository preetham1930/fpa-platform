from typing import Optional, Tuple
from backend.models import AccountType

def calculate_variance(budget: float, actual: float, account_type: AccountType) -> Tuple[float, Optional[float], bool]:
    """
    Calculates variance, variance percentage, and whether it's favorable.
    
    Rules:
    - variance = actual - budget
    - REVENUE: over-budget is favorable (actual > budget -> favorable)
    - COST: over-budget is unfavorable (actual > budget -> unfavorable)
    - budget = 0 -> variance % is None (to avoid division by zero)
    - actual == budget -> variance = 0, treated as favorable (neutral)
    """
    variance = actual - budget
    
    variance_percentage: Optional[float] = None
    if budget != 0:
        variance_percentage = (variance / abs(budget)) * 100
        
    if account_type == AccountType.revenue:
        is_favorable = variance >= 0
    else:  # AccountType.cost
        is_favorable = variance <= 0
        
    return variance, variance_percentage, is_favorable
