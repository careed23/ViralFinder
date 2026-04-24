import httpx
import asyncio
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    DATE_RANGE_START, DATE_RANGE_END, EXCLUDED_DOMAINS,
    REQUEST_DELAY_SECONDS, MAX_CONCURRENT_REQUESTS
)

# Placeholder for CandidateDomain model (will be defined in models/domain_result.py)
class CandidateDomain:
    def __init__(self, title, url, domain, post_date, upvote_count, comment_count, source):
        self.title = title
        self.url = url
        self.domain = domain
        self.post_date = post_date
        self.upvote_count = upvote_count
        self.comment_count = comment_comment
        self.source = source

    def __repr__(self):
        return f"CandidateDomain(domain='{self.domain}', title='{self.title[:30]}...')"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_hacker_news_page(session, params):
    url = "https://hn.algolia.com/api/v1/search_by_date"
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        return await response.json()


async def get_hackernews_posts():
    candidate_domains = []
    start_date = datetime.strptime(DATE_RANGE_START, "%Y-%m-%d")
    end_date = datetime.strptime(DATE_RANGE_END, "%Y-%m-%d")

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    async with httpx.AsyncClient() as session:
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
            data = await fetch_hacker_news_page(session, params)
            hits = data.get("hits", [])

            if not hits:
                break

            for hit in hits:
                title = hit.get("title")
                url = hit.get("url")
                domain = hit.get("url_without_protocol") # Algolia provides this
                created_at_i = hit.get("created_at_i")
                points = hit.get("points")
                num_comments = hit.get("num_comments")

                if not all([title, url, domain, created_at_i, points, num_comments]):
                    continue

                # Filter to include only "Show HN:" prefixed titles.
                if not title.startswith("Show HN:"):
                    continue

                # Filter out excluded domains
                if any(excluded_domain in domain for excluded_domain in EXCLUDED_DOMAINS):
                    continue

                post_date = datetime.fromtimestamp(created_at_i)

                candidate_domains.append(CandidateDomain(
                    title=title,
                    url=url,
                    domain=domain,
                    post_date=post_date,
                    upvote_count=points,
                    comment_count=num_comments,
                    source="Hacker News"
                ))
            page += 1
            await asyncio.sleep(REQUEST_DELAY_SECONDS) # Rate limit

    return candidate_domains


if __name__ == "__main__":
    async def main():
        domains = await get_hackernews_posts()
        for domain in domains:
            print(domain)

    asyncio.run(main())
