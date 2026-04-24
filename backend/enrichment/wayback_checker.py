import httpx
import asyncio
import json
from datetime import datetime
from bs4 import BeautifulSoup
from cachetools import cached, TTLCache

from config import DATE_RANGE_START, DATE_RANGE_END, REQUEST_DELAY_SECONDS

# Cache Wayback results for 24 hours
wayback_cache = TTLCache(maxsize=1000, ttl=3600 * 24)

class WaybackResult:
    def __init__(self, domain, total_snapshots=0, peak_activity_year=None, first_snapshot_date=None, last_snapshot_date=None, is_product_site=False, page_title=None, meta_description=None):
        self.domain = domain
        self.total_snapshots = total_snapshots
        self.peak_activity_year = peak_activity_year
        self.first_snapshot_date = first_snapshot_date
        self.last_snapshot_date = last_snapshot_date
        self.is_product_site = is_product_site
        self.page_title = page_title
        self.meta_description = meta_description

    def to_dict(self):
        return {
            "domain": self.domain,
            "total_snapshots": self.total_snapshots,
            "peak_activity_year": self.peak_activity_year,
            "first_snapshot_date": str(self.first_snapshot_date) if self.first_snapshot_date else None,
            "last_snapshot_date": str(self.last_snapshot_date) if self.last_snapshot_date else None,
            "is_product_site": self.is_product_site,
            "page_title": self.page_title,
            "meta_description": self.meta_description
        }


@cached(cache=wayback_cache)
async def check_wayback_machine(domain: str) -> WaybackResult:
    cdx_url = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&fl=timestamp,statuscode&limit=50&from={DATE_RANGE_START.replace('-', '')}&to={DATE_RANGE_END.replace('-', '')}"
    available_url = f"https://archive.org/wayback/available?url={domain}"

    total_snapshots = 0
    snapshots_by_year = {}
    first_snapshot_date = None
    last_snapshot_date = None
    is_product_site = False
    page_title = None
    meta_description = None

    async with httpx.AsyncClient() as client:
        # Fetch CDX data
        try:
            cdx_response = await client.get(cdx_url)
            cdx_response.raise_for_status()
            cdx_data = cdx_response.json()
            
            if cdx_data and len(cdx_data) > 1: # First element is header
                total_snapshots = len(cdx_data) - 1
                for i, snapshot in enumerate(cdx_data):
                    if i == 0: continue # Skip header
                    timestamp = snapshot[0]
                    statuscode = snapshot[1]

                    if statuscode == "200":
                        year = int(timestamp[:4])
                        snapshots_by_year[year] = snapshots_by_year.get(year, 0) + 1

                        snap_date = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
                        if not first_snapshot_date or snap_date < first_snapshot_date:
                            first_snapshot_date = snap_date
                        if not last_snapshot_date or snap_date > last_snapshot_date:
                            last_snapshot_date = snap_date

                if snapshots_by_year:
                    peak_activity_year = max(snapshots_by_year, key=snapshots_by_year.get)

        except httpx.HTTPStatusError as e:
            print(f"CDX API error for {domain}: {e}")
        except json.JSONDecodeError:
            print(f"CDX API returned invalid JSON for {domain}")
        except Exception as e:
            print(f"Error fetching CDX data for {domain}: {e}")

        await asyncio.sleep(REQUEST_DELAY_SECONDS)

        # Fetch available snapshot and analyze content
        try:
            available_response = await client.get(available_url)
            available_response.raise_for_status()
            available_data = available_response.json()

            if available_data and available_data.get("archived_snapshots", {}).get("closest"):
                snapshot_url = available_data["archived_snapshots"]["closest"]["url"]
                
                # Fetch HTML of the cached version
                html_response = await client.get(snapshot_url)
                html_response.raise_for_status()
                soup = BeautifulSoup(html_response.text, "lxml")

                if soup.title:
                    page_title = soup.title.string
                
                meta_description_tag = soup.find("meta", attrs={'name': 'description'})
                if meta_description_tag:
                    meta_description = meta_description_tag.get('content')

                # Check for e-commerce indicators
                ecommerce_keywords = ["buy", "shop", "cart", "order", "add to", "price", "$"]
                page_text = soup.get_text().lower()
                if any(keyword in page_text for keyword in ecommerce_keywords):
                    is_product_site = True

        except httpx.HTTPStatusError as e:
            print(f"Wayback Available API error for {domain}: {e}")
        except Exception as e:
            print(f"Error fetching Wayback available data for {domain}: {e}")

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
        test_domains = ["google.com", "example.com", "viralfinder.com"]
        results = await asyncio.gather(*[check_wayback_machine(d) for d in test_domains])
        for res in results:
            print(res.to_dict())

    asyncio.run(main())
