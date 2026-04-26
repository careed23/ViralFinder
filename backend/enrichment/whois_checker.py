import asyncio
import whois
import httpx
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from cachetools import cached, TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

from config import MAX_CONCURRENT_REQUESTS

# Cache WHOIS results for 24 hours
whois_cache = TTLCache(maxsize=1000, ttl=3600 * 24)

class WhoisResult:
    def __init__(self, domain, is_available, registrar=None, creation_date=None, expiration_date=None, last_updated=None, status=None, expiry_status=None, method=None):
        self.domain = domain
        self.is_available = is_available
        self.method = method
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
            "method": self.method,
            "registrar": self.registrar,
            "expiration_date": str(self.expiration_date) if self.expiration_date else None,
            "expiry_status": self.expiry_status
        }

# 1. Create a shared lock (Allowing only 1 concurrent requests max)
RDAP_SEMAPHORE = asyncio.Semaphore(1)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
async def _perform_rdap_lookup(domain: str):
    # 2. Force tasks to wait in line here
    async with RDAP_SEMAPHORE:
        # 3. Add a mandatory delay between each request
        await asyncio.sleep(1.5)
        url = f"https://rdap.org/domain/{domain}"
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            registrar = None
            for entity in data.get("entities", []):
                if "registrar" in entity.get("roles", []):
                    registrar = entity.get("vcardArray", [None, [["fn", {}, "text", ""]]])[1][0][3]
            
            expiration_date = None
            for event in data.get("events", []):
                if event.get("eventAction") == "expiration":
                    expiration_date = datetime.fromisoformat(event.get("eventDate").replace("Z", "+00:00"))

            return WhoisResult(
                domain=domain,
                is_available=False,
                method="rdap",
                registrar=registrar,
                expiration_date=expiration_date,
                expiry_status="TAKEN"
            )
        elif response.status_code == 404:
            return WhoisResult(domain, is_available=True, method="rdap", expiry_status="AVAILABLE")
        else:
            response.raise_for_status()

def fallback_whois(domain: str):
    try:
        # This is where the library is crashing internally
        result = whois.whois(domain)
        return result
    except Exception as e:
        # Catch the internal library crash and print it, but keep the app alive
        print(f"WHOIS library failed for {domain} - skipping. Error: {e}")
        return None

def _perform_whois_lookup(domain):
    try:
        w = fallback_whois(domain)
        if w is None:
            return WhoisResult(domain, is_available=False, method="whois", expiry_status="UNKNOWN")

        if getattr(w, 'status', None) is None or getattr(w, 'domain_name', None) is None:
            return WhoisResult(domain, is_available=True, method="whois", expiry_status="AVAILABLE")
        else:
            expiration_date = w.expiration_date
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0]

            return WhoisResult(
                domain=domain,
                is_available=False,
                method="whois",
                registrar=w.registrar,
                expiration_date=expiration_date,
                expiry_status="TAKEN"
            )
    except Exception as e:
        print(f"WHOIS lookup failed for {domain}: {e}")
        return WhoisResult(domain, is_available=False, method="whois", expiry_status="UNKNOWN")

@cached(cache=whois_cache)
async def check_whois(domain: str) -> WhoisResult:
    try:
        result = await _perform_rdap_lookup(domain)
    except Exception as e:
        print(f"RDAP lookup for {domain} failed: {e}. Falling back to WHOIS.")
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            result = await loop.run_in_executor(executor, _perform_whois_lookup, domain)
            
    result.registrar_check_url = f"https://www.namecheap.com/domains/registration/results/?domain={domain}"
    return result

if __name__ == "__main__":
    async def main():
        test_domains = ["google.com", "example.com", "thisdomainisdefinitelynotregistered12345.com"]
        results = await asyncio.gather(*[check_whois(d) for d in test_domains])
        for res in results:
            print(res.to_dict())

    asyncio.run(main())
