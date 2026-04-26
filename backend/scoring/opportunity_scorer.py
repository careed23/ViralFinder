from typing import Dict, Any, Optional
from pydantic import BaseModel

class ScoreResult(BaseModel):
    score: float
    factors: Dict[str, float]

async def calculate_opportunity_score(
    domain: str, 
    whois_result: Any, 
    wayback_result: Any, 
    authority_result: Any, 
    trademark_result: Any,
    candidate_data: Dict[str, Any]
) -> ScoreResult:
    
    score = 0.0
    factors = {}

    # 1. Availability & Expiry Status (Weight: 0.3)
    if getattr(whois_result, 'expiry_status', None) == "AVAILABLE":
        factors['availability'] = 0.3
    elif getattr(whois_result, 'expiry_status', None) == "EXPIRING_SOON":
        factors['availability'] = 0.2
    else:
        factors['availability'] = 0.0
    
    # 2. Wayback History / Age (Weight: 0.3)
    # THE FIX: Safe integer conversion with defaults
    try:
        current_year = 2024
        # Use getattr with default 0, then ensure it's an int
        peak_year = wayback_result.peak_activity_year
        peak_year = int(peak_year) if peak_year is not None else 0
        
        if peak_year > 0:
            age = current_year - peak_year
            # Higher score for older "vintage" domains (10+ years)
            age_factor = min(age / 20.0, 1.0) * 0.3
            factors['age'] = round(age_factor, 2)
        else:
            factors['age'] = 0.0
    except (ValueError, TypeError):
        factors['age'] = 0.0

    # 3. Product/E-commerce Signals (Weight: 0.2)
    if getattr(wayback_result, 'is_product_site', False):
        factors['product_signal'] = 0.2
    else:
        factors['product_signal'] = 0.0

    # 4. Authority & Backlinks (Weight: 0.2)
    # THE FIX: Ensure authority is handled as int safely
    try:
        da = authority_result.domain_authority
        da = int(da) if da is not None else 0
        auth_factor = min(da / 50.0, 1.0) * 0.2
        factors['authority'] = round(auth_factor, 2)
    except (ValueError, TypeError):
        factors['authority'] = 0.0

    # Calculate final score
    score = sum(factors.values())
    
    # Trademark Penalty
    if getattr(trademark_result, 'has_trademark_risk', False):
        score -= 0.5

    return ScoreResult(
        score=max(0.0, min(1.0, score)),
        factors=factors
    )