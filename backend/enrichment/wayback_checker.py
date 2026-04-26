import httpx
import asyncio
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from cachetools import cached, TTLCache

from config import SCAN_DATE_FROM, SCAN_DATE_TO, REQUEST_DELAY_SECONDS

# Cache Wayback results for 24 hours
wayback_cache = TTLCache(maxsize=1000, ttl=3600 * 24)

class WaybackResult:
    def __init__(self, domain, total_snapshots=0, peak_activity_year=0, 
                 first_snapshot_date=None, last_snapshot_date=None, 
                 is_product_site=False, page_title="", meta_description=""):
        self.domain = domain
        self.total_snapshots = total_snapshots
        self.peak_activity_year = peak_activity_year
        self.first_snapshot_date = first_snapshot_date
        self.last_snapshot_date = last_snapshot_date
        self.is_product_site = is_product_site
        self.page_title = page_title
        self.meta_description = meta_description
        
        # Compatibility aliases for scoring and models
        self.snapshot_count = total_snapshots
        self.has_product_signals = is_product_site
        self.payment_processor = None
        self.price_found = None
        self.product_keywords = []

    def to_dict(self):
        return {
            "domain": self.domain,
            "total_snapshots": self.total_snapshots,
            "peak_activity_year": self.peak_activity_year,
            "first_snapshot_date": self.first_snapshot_date.isoformat() if self.first_snapshot_date else None,
            "last_snapshot_date": self.last_snapshot_date.isoformat() if self.last_snapshot_date else None,
            "is_product_site": self.is_product_site,
            "page_title": self.page_title,
            "meta_description": self.meta_description
        }

semaphore = asyncio.Semaphore(2)

@cached(cache=wayback_cache)
async def check_wayback_machine(domain: str) -> WaybackResult:
    cdx_url = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&fl=timestamp,statuscode&limit=50&from={SCAN_DATE_FROM.replace('-', '')}&to={SCAN_DATE_TO.replace('-', '')}"
    available_url = f"https://archive.org/wayback/available?url={domain}"

    # Default values
    total_snapshots = 0
    snapshots_by_year = {}
    peak_activity_year = 0 
    first_snapshot_date = None
    last_snapshot_date = None
    is_product_site = False
    page_title = ""
    meta_description = ""

    # FAST-FAIL TIMEOUT: 5 seconds is plenty for a healthy API
    TIMEOUT = httpx.Timeout(5.0, connect=2.0)

    async with semaphore:
        await asyncio.sleep(1) # Politeness delay
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # --- PHASE 1: CDX HISTORY SCAN ---
            try:
                cdx_response = await client.get(cdx_url)
                
                # Check for rate limiting or service unavailability
                if cdx_response.status_code in [429, 503]:
                    logging.warning(f"Wayback Throttled (503/429) for {domain}. Skipping history.")
                    return WaybackResult(domain=domain)

                cdx_response.raise_for_status()
                cdx_data = cdx_response.json()
            
                if isinstance(cdx_data, list) and len(cdx_data) > 1:
                    for row in cdx_data[1:]: # Skip header
                        if not row or len(row) < 2:
                            continue

                        timestamp = row[0]
                        statuscode = row[1]

                        # TYPE GUARD: Ensure timestamp is a valid string
                        if statuscode == "200" and isinstance(timestamp, str) and len(timestamp) >= 4:
                            try:
                                year_str = timestamp[:4]
                                if year_str.isdigit():
                                    year_val = int(year_str)
                                    snapshots_by_year[year_val] = snapshots_by_year.get(year_val, 0) + 1

                                    if len(timestamp) >= 14:
                                        snap_date = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
                                        if not first_snapshot_date or snap_date < first_snapshot_date:
                                            first_snapshot_date = snap_date
                                        if not last_snapshot_date or snap_date > last_snapshot_date:
                                            last_snapshot_date = snap_date
                            except (ValueError, TypeError):
                                continue

                    if snapshots_by_year:
                        peak_activity_year = max(snapshots_by_year, key=snapshots_by_year.get)
                        total_snapshots = sum(snapshots_by_year.values())
            except Exception as e:
                logging.error(f"Wayback CDX skip for {domain}: {e}")

            # --- PHASE 2: CONTENT ANALYSIS (SNAPSHOT SCRAPING) ---
            try:
                # Add a small delay between calls to avoid triggering another 503
                await asyncio.sleep(0.5)
                available_response = await client.get(available_url)
                
                if available_response.status_code in [429, 503]:
                    return WaybackResult(domain=domain, total_snapshots=total_snapshots, peak_activity_year=peak_activity_year)

                available_response.raise_for_status()
                available_data = available_response.json()

                closest = available_data.get("archived_snapshots", {}).get("closest")
                if closest and closest.get("url"):
                    snapshot_url = closest["url"]
                    
                    html_response = await client.get(snapshot_url)
                    html_response.raise_for_status()
                    soup = BeautifulSoup(html_response.text, "lxml")

                    if soup.title:
                        page_title = str(soup.title.string or "").strip()
                    
                    meta_tag = soup.find("meta", attrs={'name': 'description'})
                    if meta_tag:
                        meta_description = str(meta_tag.get('content') or "").strip()

                    ecommerce_keywords = ["buy", "shop", "cart", "order", "add to", "price", "$"]
                    page_text = soup.get_text().lower()
                    if any(kw in page_text for kw in ecommerce_keywords):
                        is_product_site = True
            except Exception as e:
                logging.debug(f"Wayback Content skip for {domain}: {e}")

        return WaybackResult(
            domain=domain,
            total_snapshots=total_snapshots,
            peak_activity_year=peak_activity_year,
            first_snapshot_date=first_snapshot_date,
            last_snapshot_date=last_snapshot_date,
            is_product_site=is_product_site,
            page_title=page_title,
            meta_description=meta_description
        )

if __name__ == "__main__":
    async def main():
        test_domains = ["google.com"]
        results = await asyncio.gather(*[check_wayback_machine(d) for d in test_domains])
        for res in results:
            print(res.to_dict())

    asyncio.run(main())