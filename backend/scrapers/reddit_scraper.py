import os
import re
import praw
import asyncio
from datetime import datetime
from urllib.parse import urlparse
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from config import (
    VIRAL_SUBREDDITS,
    EXCLUDED_DOMAINS,
    REQUEST_DELAY_SECONDS,
    MAX_CONCURRENT_REQUESTS,
    SCAN_DATE_FROM,
    SCAN_DATE_TO,
)
from models.domain_result import CandidateDomain

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "ViralFinder v1.0"


def get_reddit_instance():
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def extract_domain_from_url(url):
    try:
        parsed_uri = urlparse(url)
        domain = "{uri.netloc}".format(uri=parsed_uri)
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def search_subreddit(reddit, subreddit_name, start_date, end_date):
    subreddit = reddit.subreddit(subreddit_name)
    results = []
    
    # PRAW's search is not great for date ranges, so we'll have to filter manually.
    # We will search for a generic query and then filter by date.
    for submission in subreddit.search('url', limit=1000):
        created_date = datetime.fromtimestamp(submission.created_utc)
        if not (start_date <= created_date <= end_date):
            continue

        if submission.score < 100:
            continue

        # Check for URL in post body
        urls = re.findall(r"(https?://[^\s]+)", submission.selftext)
        # Check for URL in top-level comments
        submission.comments.replace_more(limit=0)
        for comment in submission.comments:
            urls.extend(re.findall(r"(https?://[^\s]+)", comment.body))
            
        if submission.url:
            urls.append(submission.url)

        for url in urls:
            domain = extract_domain_from_url(url)
            if domain and all(
                exc_domain not in domain for exc_domain in EXCLUDED_DOMAINS
            ):
                results.append(
                    CandidateDomain(
                        title=submission.title,
                        url=url,
                        domain=domain,
                        post_date=created_date,
                        upvote_count=submission.score,
                        comment_count=submission.num_comments,
                        subreddit=subreddit_name,
                        permalink=f"https://www.reddit.com{submission.permalink}",
                        source="Reddit"
                    )
                )
    return results

async def get_reddit_posts():
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("Reddit API credentials not found. Skipping Reddit scraper.")
        return []

    reddit = get_reddit_instance()
    
    start_date = datetime.strptime(SCAN_DATE_FROM, "%Y-%m-%d")
    end_date = datetime.strptime(SCAN_DATE_TO, "%Y-%m-%d")

    tasks = [
        search_subreddit(reddit, sub, start_date, end_date)
        for sub in VIRAL_SUBREDDITS
    ]
    
    all_domains = await asyncio.gather(*tasks)
    
    # Flatten list of lists
    return [item for sublist in all_domains for item in sublist]

if __name__ == "__main__":
    async def main():
        domains = await get_reddit_posts()
        for domain in domains:
            print(domain)

    asyncio.run(main())
