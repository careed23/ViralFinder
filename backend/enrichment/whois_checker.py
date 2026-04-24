import asyncio
import whois
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from cachetools import cached, TTLCache

from config import MAX_CONCURRENT_REQUESTS

# Cache WHOIS results for 24 hours
whois_cache = TTLCache(maxsize=1000, ttl=3600 * 24)

class WhoisResult:
    def __init__(self, domain, is_available, registrar=None, creation_date=None, expiration_date=None, last_updated=None, status=None, expiry_status=None):
        self.domain = domain
        self.is_available = is_available
        self.registrar = registrar
        self.creation_date = creation_date
        self.expiration_date = expiration_date
        self.last_updated = last_updated
        self.status = status
        self.expiry_status = expiry_status # AVAILABLE, EXPIRING_SOON, TAKEN

    def to_dict(self):
        return {
            "domain": self.domain,
            "is_available": self.is_available,
            "registrar": self.registrar,
            "creation_date": str(self.creation_date) if self.creation_date else None,
            "expiration_date": str(self.expiration_date) if self.expiration_date else None,
            "last_updated": str(self.last_updated) if self.last_updated else None,
            "status": self.status,
            "expiry_status": self.expiry_status
        }


async def _perform_whois_lookup(domain):
    try:
        w = whois.whois(domain)
        if w.status is None or w.domain_name is None:
            return WhoisResult(domain, is_available=True, expiry_status="AVAILABLE")
        else:
            expiration_date = w.expiration_date
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0]

            is_available = False
            expiry_status = "TAKEN"
            if expiration_date and isinstance(expiration_date, datetime):
                if expiration_date < datetime.now() + timedelta(days=30):
                    expiry_status = "EXPIRING_SOON"
            
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]

            last_updated = w.updated_date
            if isinstance(last_updated, list):
                last_updated = last_updated[0]

            return WhoisResult(
                domain=domain,
                is_available=is_available,
                registrar=w.registrar,
                creation_date=creation_date,
                expiration_date=expiration_date,
                last_updated=last_updated,
                status=w.status,
                expiry_status=expiry_status
            )
    except Exception as e:
        # Handle cases where WHOIS lookup fails (e.g., domain not found, rate limiting)
        print(f"WHOIS lookup failed for {domain}: {e}")
        return WhoisResult(domain, is_available=False, expiry_status="UNKNOWN")


@cached(cache=whois_cache)
async def check_whois(domain: str) -> WhoisResult:
    loop = asyncio.get_running_loop()
    # python-whois is blocking, so run it in a thread pool
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        result = await loop.run_in_executor(executor, _perform_whois_lookup, domain)
    return result


if __name__ == "__main__":
    async def main():
        test_domains = ["google.com", "example.com", "thisdomainisdefinitelynotregistered12345.com"]
        results = await asyncio.gather(*[check_whois(d) for d in test_domains])
        for res in results:
            print(res.to_dict())

    asyncio.run(main())
