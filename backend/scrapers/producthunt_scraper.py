import os
import httpx
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    SCAN_DATE_FROM, SCAN_DATE_TO, PRODUCTHUNT_TOPICS,
    EXCLUDED_DOMAINS, REQUEST_DELAY_SECONDS
)

# Force load the .env from the root
load_dotenv() 

# Get the token using the KEY name from your .env file
PRODUCTHUNT_API_TOKEN = 'mt2KdK9Iy8RwB0Z6IzieHxcPvZeLRLGBwhUZ2AbVS8Q'

# Placeholder for CandidateDomain model
class CandidateDomain:
    def __init__(self, title, url, domain, post_date, upvote_count, comment_count, source, topics=None):
        self.title = title
        self.url = url
        self.domain = domain
        self.post_date = post_date
        self.upvote_count = upvote_count
        self.comment_count = comment_count
        self.source = source
        self.topics = topics if topics is not None else []

    def __repr__(self):
        return f"CandidateDomain(domain='{self.domain}', title='{self.title[:30]}...')"


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=5, max=60))
async def fetch_producthunt_posts_page(session, cursor=None):
    url = "https://api.producthunt.com/v2/api/graphql"
    
    # Ensure token is present before sending
    if not PRODUCTHUNT_API_TOKEN:
        print("CRITICAL: PRODUCTHUNT_API_TOKEN is missing from your environment!")
        return {"data": {"posts": {"edges": [], "pageInfo": {"hasNextPage": False}}}}

    headers = {
        "Authorization": f"Bearer {PRODUCTHUNT_API_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    query ($cursor: String, $postedAfter: DateTime, $postedBefore: DateTime) {
      posts(order: VOTES, postedAfter: $postedAfter, postedBefore: $postedBefore, after: $cursor) {
        edges {
          node {
            id
            name
            tagline
            url
            website
            votesCount
            commentsCount
            createdAt
            topics { edges { node { name } } }
          }
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
    """

    variables = {
        "postedAfter": SCAN_DATE_FROM + "T00:00:00Z",
        "postedBefore": SCAN_DATE_TO + "T23:59:59Z"
    }
    if cursor:
        variables["cursor"] = cursor

    payload = {"query": query, "variables": variables}

    # FIX: Await the post call directly and check status
    response = await session.post(url, headers=headers, json=payload)
    
    if response.status_code == 401:
        print("DEBUG: 401 Unauthorized - Check your token string in the .env file.")
        
    response.raise_for_status()
    # FIX: httpx response.json() is NOT a coroutine, do not await it
    return response.json()


async def get_producthunt_posts():
    candidate_domains = []
    async with httpx.AsyncClient(timeout=30.0) as session:
        cursor = None
        has_next_page = True

        while has_next_page:
            try:
                data = await fetch_producthunt_posts_page(session, cursor)
                posts_data = data.get("data", {}).get("posts", {})
                edges = posts_data.get("edges", [])
                page_info = posts_data.get("pageInfo", {})

                for edge in edges:
                    node = edge.get("node", {})
                    name = node.get("name")
                    url = node.get("url")
                    website = node.get("website")
                    votes_count = node.get("votesCount")
                    comments_count = node.get("commentsCount")
                    created_at = node.get("createdAt")
                    topics_data = node.get("topics", {}).get("edges", [])
                    topics = [t.get("node", {}).get("name") for t in topics_data if t.get("node", {}).get("name")]

                    if not all([name, url, website, votes_count, comments_count, created_at]):
                        continue

                    # Filter posts with votesCount >= 50 for better discovery
                    if votes_count < 50:
                        continue

                    # Filter by topics
                    if not any(topic in PRODUCTHUNT_TOPICS for topic in topics):
                        continue

                    # Extract domain from website URL
                    domain = website.split("//")[-1].split("/")[0] if website else None
                    if not domain:
                        continue

                    # Filter out excluded domains (social media, etc.)
                    if any(excluded_domain in domain for excluded_domain in EXCLUDED_DOMAINS):
                        continue

                    post_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

                    candidate_domains.append(CandidateDomain(
                        title=name,
                        url=url,
                        domain=domain,
                        post_date=post_date,
                        upvote_count=votes_count,
                        comment_count=comments_count,
                        source="Product Hunt",
                        topics=topics
                    ))
                
                cursor = page_info.get("endCursor")
                has_next_page = page_info.get("hasNextPage", False)
                
                if has_next_page:
                    await asyncio.sleep(REQUEST_DELAY_SECONDS)

            except Exception as e:
                print(f"Scraper Error: {e}")
                break

    return candidate_domains


if __name__ == "__main__":
    async def main():
        print("Starting Product Hunt Scrape...")
        domains = await get_producthunt_posts()
        print(f"Found {len(domains)} candidate domains.")
        for domain in domains:
            print(domain)

    asyncio.run(main())