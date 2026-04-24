import httpx
import asyncio
from bs4 import BeautifulSoup
import re
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    PRODUCT_KEYWORDS, REQUEST_DELAY_SECONDS
)

# Placeholder for CandidateDomain model (will be defined in models/domain_result.py)
class CandidateDomain:
    def __init__(self, domain, source, domain_age=None, backlinks_count=None, alexa_rank=None, available_status=None):
        self.domain = domain
        self.source = source
        self.domain_age = domain_age
        self.backlinks_count = backlinks_count
        self.alexa_rank = alexa_rank
        self.available_status = available_status

    def __repr__(self):
        return f"CandidateDomain(domain='{self.domain}', source='{self.source}')"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_expired_domains_page(session, url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        return await response.text()


async def get_expired_domains():
    candidate_domains = []
    target_url = "https://www.expireddomains.net/deleted-com-domains/"

    async with httpx.AsyncClient() as session:
        html_content = await fetch_expired_domains_page(session, target_url)
        soup = BeautifulSoup(html_content, "lxml")

        # Find the table containing domain data
        # This might need adjustment based on the actual HTML structure
        domain_table = soup.find("table", {"class": "domain-list"})
        if not domain_table:
            print("Could not find domain list table.")
            return []

        rows = domain_table.find("tbody").find_all("tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 10: # Assuming at least 10 columns for relevant data
                continue

            domain_name = cols[0].text.strip()
            domain_age = int(cols[2].text.strip()) if cols[2].text.strip().isdigit() else None
            backlinks_count = int(cols[5].text.strip()) if cols[5].text.strip().isdigit() else None
            alexa_rank = int(cols[7].text.strip()) if cols[7].text.strip().isdigit() else None
            available_status = cols[9].text.strip() # This column might vary

            # Filter by product keywords
            if not any(keyword in domain_name.lower() for keyword in PRODUCT_KEYWORDS):
                continue

            candidate_domains.append(CandidateDomain(
                domain=domain_name,
                source="ExpiredDomains.net",
                domain_age=domain_age,
                backlinks_count=backlinks_count,
                alexa_rank=alexa_rank,
                available_status=available_status
            ))
            
            await asyncio.sleep(REQUEST_DELAY_SECONDS) # Rate limit

    return candidate_domains


if __name__ == "__main__":
    async def main():
        domains = await get_expired_domains()
        for domain in domains:
            print(domain)

    asyncio.run(main())
