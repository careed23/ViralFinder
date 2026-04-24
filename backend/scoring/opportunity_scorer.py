from datetime import datetime
from config import SCORING_WEIGHTS
from enrichment.whois_checker import WhoisResult
from enrichment.wayback_checker import WaybackResult
from enrichment.authority_checker import AuthorityResult
from enrichment.trademark_checker import TrademarkResult

class OpportunityScore:
    def __init__(self, domain, score, details):
        self.domain = domain
        self.score = score
        self.details = details

    def to_dict(self):
        return {
            "domain": self.domain,
            "score": self.score,
            "details": self.details
        }


async def calculate_opportunity_score(
    domain: str,
    whois_result: WhoisResult,
    wayback_result: WaybackResult,
    authority_result: AuthorityResult,
    trademark_result: TrademarkResult
) -> OpportunityScore:
    score = 0.0
    details = {}

    # Domain Age (from WHOIS creation_date)
    if whois_result.creation_date:
        domain_age_years = (datetime.now() - whois_result.creation_date).days / 365.25
        # Older domains get higher scores (cap at 10 years)
        score += min(domain_age_years / 10, 1.0) * SCORING_WEIGHTS["domain_age"]
        details["domain_age_years"] = round(domain_age_years, 1)

    # Wayback Snapshots (primary indicator of site activity)
    if wayback_result.total_snapshots:
        # Score based on snapshot count (normalize to 0-1, cap at 200 snapshots)
        snapshot_score = min(wayback_result.total_snapshots / 200, 1.0)
        score += snapshot_score * SCORING_WEIGHTS["wayback_snapshots"]
        details["wayback_snapshots"] = wayback_result.total_snapshots

    # E-commerce Indicators (shows it was a product/shop site)
    if wayback_result.is_product_site:
        score += SCORING_WEIGHTS["ecommerce_indicators"]
        details["ecommerce_indicators"] = True
    else:
        details["ecommerce_indicators"] = False

    # Peak Activity Year (recent peak activity is better)
    if wayback_result.peak_activity_year:
        # Sites that peaked 2014-2019 get full score, older gets less
        years_since_peak = datetime.now().year - wayback_result.peak_activity_year
        peak_score = max(0, min(1.0, (10 - years_since_peak) / 10))
        score += peak_score * SCORING_WEIGHTS["peak_activity"]
        details["peak_activity_year"] = wayback_result.peak_activity_year
        details["years_since_peak"] = years_since_peak

    # Trademark Risk (negative score)
    if trademark_result.has_trademark_risk:
        score += SCORING_WEIGHTS["trademark_risk"]
        details["has_trademark_risk"] = True
    else:
        details["has_trademark_risk"] = False

    # Ensure score is between 0 and 1
    score = max(0.0, min(1.0, score))

    return OpportunityScore(domain, round(score, 3), details)


if __name__ == "__main__":
    from datetime import datetime, timedelta

    async def main():
        # Example Usage
        domain = "example.com"
        whois_res = WhoisResult(
            domain=domain,
            is_available=False,
            creation_date=datetime.now() - timedelta(days=365 * 5),
            expiration_date=datetime.now() + timedelta(days=365),
            expiry_status="TAKEN"
        )
        wayback_res = WaybackResult(
            domain=domain,
            total_snapshots=250,
            is_product_site=True
        )
        authority_res = AuthorityResult(
            domain=domain,
            domain_authority=70,
            page_authority=60,
            linking_root_domains=500,
            total_links=1500
        )
        trademark_res = TrademarkResult(domain, has_trademark_risk=False)

        opportunity_score = await calculate_opportunity_score(
            domain, whois_res, wayback_res, authority_res, trademark_res
        )
        print(opportunity_score.to_dict())

        domain_risky = "trademarkedbrand.com"
        whois_res_risky = WhoisResult(
            domain=domain_risky,
            is_available=False,
            creation_date=datetime.now() - timedelta(days=365 * 2),
            expiration_date=datetime.now() + timedelta(days=365),
            expiry_status="TAKEN"
        )
        wayback_res_risky = WaybackResult(
            domain=domain_risky,
            total_snapshots=50,
            is_product_site=False
        )
        authority_res_risky = AuthorityResult(
            domain=domain_risky,
            domain_authority=30,
            page_authority=20,
            linking_root_domains=50,
            total_links=100
        )
        trademark_res_risky = TrademarkResult(domain_risky, has_trademark_risk=True, details="Registered trademark found")

        opportunity_score_risky = await calculate_opportunity_score(
            domain_risky, whois_res_risky, wayback_res_risky, authority_res_risky, trademark_res_risky
        )
        print(opportunity_score_risky.to_dict())

    import asyncio
    asyncio.run(main())
