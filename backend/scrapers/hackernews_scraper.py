import httpx
import asyncio
from datetime import datetime
from urllib.parse import urlparse
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    SCAN_DATE_FROM, SCAN_DATE_TO, EXCLUDED_DOMAINS,
    REQUEST_DELAY_SECONDS, MAX_CONCURRENT_REQUESTS
)

# Placeholder for CandidateDomain model
class CandidateDomain:
    def __init__(self, title, url, domain, post_date, upvote_count, comment_count, source):
        self.title = title
        self.url = url
        self.domain = domain
        self.post_date = post_date
        self.upvote_count = upvote_count
        self.comment_count = comment_count # FIX: Fixed the 'comment_comment' typo
        self.source = source

    def __repr__(self):
        return f"CandidateDomain(domain='{self.domain}', title='{self.title[:30]}...')"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_hacker_news_page(session, params):
    url = "https://hn.algolia.com/api/v1/search_by_date"
    
    # FIX: Corrected the httpx async syntax 
    response = await session.get(url, params=params)
    response.raise_for_status()
    
    # FIX: Removed await from response.json()
    return response.json()


async def get_hackernews_posts():
    candidate_domains = []
    start_date = datetime.strptime(SCAN_DATE_FROM, "%Y-%m-%d")
    end_date = datetime.strptime(SCAN_DATE_TO, "%Y-%m-%d")

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    async with httpx.AsyncClient(timeout=30.0) as session:
        page = 0
        while True:
            params = {
                "query": "Show HN",
                "tags": "story",
                "numericFilters": [
                    f"created_at_i>={start_timestamp}",
                    f"created_at_i<={end_timestamp}",
                    "points>=100"
                ],
                "hitsPerPage": 1000,
                "page": page
            }
            try:
                data = await fetch_hacker_news_page(session, params)
                hits = data.get("hits", [])

                if not hits:
                    break

                for hit in hits:
                    # Extract data from hit
                    title = hit.get("title", "")
                    url = hit.get("url", "")
                    created_at_i = hit.get("created_at_i")
                    points = hit.get("points", 0)
                    num_comments = hit.get("num_comments", 0)
                    
                    # Validate required fields
                    if not title or not url or not created_at_i:
                        continue
                    
                    # Extract domain using urlparse for better reliability
                    try:
                        parsed = urlparse(url)
                        domain = parsed.netloc or parsed.path.split('/')[0]
                        # Remove port numbers if present
                        domain = domain.split(':')[0]
                        # Strip 'www.' for cleaner WHOIS lookups
                        domain = domain.replace("www.", "")
                    except Exception:
                        continue
                    
                    # Skip if no valid domain extracted
                    if not domain:
                        continue
                    
                    # Skip Hacker News internal routing links
                    if "ycombinator.com" in domain:
                        continue

                    # Filter out excluded domains
                    if any(excluded_domain in domain for excluded_domain in EXCLUDED_DOMAINS):
                        continue

                    # Convert timestamp to datetime
                    post_date = datetime.fromtimestamp(created_at_i)

                    # Create and append the candidate domain
                    candidate_domains.append(CandidateDomain(
                        title=title,
                        url=url,
                        domain=domain,
                        post_date=post_date,
                        upvote_count=points,
                        comment_count=num_comments,
                        source="Hacker News"
                    ))
                
                print(f"Hacker News: Scraped page {page} successfully.")
                page += 1
                await asyncio.sleep(REQUEST_DELAY_SECONDS) # Rate limit
                
            except Exception as e:
                print(f"Hacker News Scraper Error: {e}")
                break

    print(f"SUCCESS: Hacker News completely finished! Returning {len(candidate_domains)} domains to the main job.")
    return candidate_domains


if __name__ == "__main__":
    async def main():
        print("Starting Hacker News Scrape...")
        domains = await get_hackernews_posts()
        print(f"Found {len(domains)} candidate domains.")
        for domain in domains:
            print(domain)

    asyncio.run(main())