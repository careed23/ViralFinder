import os
import re
import asyncio
import httpx
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    DATE_RANGE_START, DATE_RANGE_END, VIRAL_SUBREDDITS,
    EXCLUDED_DOMAINS, REQUEST_DELAY_SECONDS, MAX_CONCURRENT_REQUESTS
)

# Placeholder for CandidateDomain model (will be defined in models/domain_result.py)
class CandidateDomain:
    def __init__(self, title, url, domain, post_date, upvote_count, comment_count, subreddit, permalink):
        self.title = title
        self.url = url
        self.domain = domain
        self.post_date = post_date
        self.upvote_count = upvote_count
        self.comment_count = comment_count
        self.subreddit = subreddit
        self.permalink = permalink

    def __repr__(self):
        return f"CandidateDomain(domain='{self.domain}', title='{self.title[:30]}...')"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_pushshift_data(subreddit, start_timestamp, end_timestamp, session, limit=500):
    url = "https://api.pushshift.io/reddit/search/submission"
    params = {
        "subreddit": subreddit,
        "after": start_timestamp,
        "before": end_timestamp,
        "size": limit,
        "score": ">=500",
        "num_comments": ">=50",
        "fields": "title,url,domain,created_utc,score,num_comments,subreddit,permalink"
    }
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        data = await response.json()
        return data.get("data", [])


async def get_reddit_posts():
    candidate_domains = []
    product_patterns = [
        re.compile(r"launched", re.IGNORECASE),
        re.compile(r"just released", re.IGNORECASE),
        re.compile(r"introducing", re.IGNORECASE),
        re.compile(r"check out", re.IGNORECASE),
        re.compile(r"made a", re.IGNORECASE),
        re.compile(r"built a", re.IGNORECASE),
        re.compile(r"show HN", re.IGNORECASE),
        re.compile(r"my product", re.IGNORECASE),
        re.compile(r"our product", re.IGNORECASE),
        re.compile(r"Kickstarter", re.IGNORECASE),
        re.compile(r"IndieGogo", re.IGNORECASE),
        re.compile(r"pre-order", re.IGNORECASE),
        re.compile(r"just shipped", re.IGNORECASE)
    ]

    start_date = datetime.strptime(DATE_RANGE_START, "%Y-%m-%d")
    end_date = datetime.strptime(DATE_RANGE_END, "%Y-%m-%d")

    # Pushshift API works with Unix timestamps
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    async with httpx.AsyncClient() as session:
        tasks = []
        for subreddit_name in VIRAL_SUBREDDITS:
            tasks.append(fetch_pushshift_data(subreddit_name, start_timestamp, end_timestamp, session))
        
        results = await asyncio.gather(*tasks)

        for posts in results:
            for post in posts:
                title = post.get("title")
                url = post.get("url")
                domain = post.get("domain")
                created_utc = post.get("created_utc")
                score = post.get("score")
                num_comments = post.get("num_comments")
                subreddit = post.get("subreddit")
                permalink = post.get("permalink")

                if not all([title, url, domain, created_utc, score, num_comments, subreddit, permalink]):
                    continue

                # Filter out excluded domains
                if any(excluded_domain in domain for excluded_domain in EXCLUDED_DOMAINS):
                    continue

                # Check for product-related patterns in title
                if not any(pattern.search(title) for pattern in product_patterns):
                    continue

                post_date = datetime.fromtimestamp(created_utc)

                candidate_domains.append(CandidateDomain(
                    title=title,
                    url=url,
                    domain=domain,
                    post_date=post_date,
                    upvote_count=score,
                    comment_count=num_comments,
                    subreddit=subreddit,
                    permalink=f"https://www.reddit.com{permalink}"
                ))
    
    return candidate_domains


if __name__ == "__main__":
    async def main():
        domains = await get_reddit_posts()
        for domain in domains:
            print(domain)

    asyncio.run(main())
