import httpx
import asyncio
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    PRODUCTHUNT_API_TOKEN, DATE_RANGE_START, DATE_RANGE_END,
    PRODUCTHUNT_TOPICS, EXCLUDED_DOMAINS, REQUEST_DELAY_SECONDS
)

# Placeholder for CandidateDomain model (will be defined in models/domain_result.py)
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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_producthunt_posts_page(session, cursor=None):
    url = "https://api.producthunt.com/v2/api/graphql"
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
        "postedAfter": DATE_RANGE_START + "T00:00:00Z",
        "postedBefore": DATE_RANGE_END + "T23:59:59Z"
    }
    if cursor:
        variables["cursor"] = cursor

    payload = {"query": query, "variables": variables}

    async with session.post(url, headers=headers, json=payload) as response:
        response.raise_for_status()
        return await response.json()


async def get_producthunt_posts():
    candidate_domains = []
    async with httpx.AsyncClient() as session:
        cursor = None
        has_next_page = True

        while has_next_page:
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

                # Filter posts with votesCount >= 200.
                if votes_count < 200:
                    continue

                # Filter by topics
                if not any(topic in PRODUCTHUNT_TOPICS for topic in topics):
                    continue

                # Extract domain from website URL
                domain = website.split("//")[-1].split("/")[0] if website else None
                if not domain:
                    continue

                # Filter out excluded domains
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
                await asyncio.sleep(REQUEST_DELAY_SECONDS) # Rate limit

    return candidate_domains


if __name__ == "__main__":
    async def main():
        # For testing, ensure PRODUCTHUNT_API_TOKEN is set in your environment or .env file
        # os.environ["PRODUCTHUNT_API_TOKEN"] = "YOUR_TOKEN_HERE"
        domains = await get_producthunt_posts()
        for domain in domains:
            print(domain)

    asyncio.run(main())
