import os
import httpx
import re
from urllib.parse import urlparse
from config import EXCLUDED_DOMAINS
from datetime import datetime

class CandidateDomain:
    def __init__(self, title, url, domain, post_date, upvote_count, comment_count, source):
        self.title = title
        self.url = url
        self.domain = domain
        self.post_date = post_date
        self.upvote_count = upvote_count
        self.comment_count = comment_count
        self.source = source

    def __repr__(self):
        return f"CandidateDomain(domain='{self.domain}', title='{self.title[:30]}...')"

async def get_youtube_urls():
    # Change this line:
    api_key = os.getenv("YOUTUBE_API_KEY") 
    
    if not api_key:
        print("Warning: YOUTUBE_API_KEY not found in environment.")
        return []
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": "unboxing|review", # Removed spaces around the pipe for better URL encoding
        "publishedAfter": "2014-01-01T00:00:00Z",
        "publishedBefore": "2018-12-31T23:59:59Z",
        "maxResults": 50,
        "order": "viewCount",
        "type": "video",
        "key": api_key
    }

    candidates = []
    seen_domains = set()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            
            # --- THE FIX: Detailed Error Interception ---
            if response.status_code != 200:
                print(f"\n--- YOUTUBE API ERROR ---")
                print(f"Status Code: {response.status_code}")
                print(f"Details: {response.text}")
                print(f"-------------------------\n")
            # --------------------------------------------
            
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            for item in items:
                snippet = item.get("snippet", {})
                description = snippet.get("description", "")
                if not description:
                    continue
                
                title = snippet.get("title", "")
                video_id = item.get("id", {}).get("videoId", "")
                video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
                published_at_str = snippet.get("publishedAt", "")
                
                try:
                    post_date = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ") if published_at_str else datetime.utcnow()
                except Exception:
                    post_date = datetime.utcnow()
                
                urls = re.findall(r'https?://[^\s<>"]+', description)
                for link in urls:
                    try:
                        parsed = urlparse(link)
                        domain = parsed.netloc or parsed.path.split('/')[0]
                        domain = domain.split(':')[0]
                        domain = domain.replace("www.", "")
                        
                        if domain and "." in domain and domain not in seen_domains:
                            if any(excluded in domain for excluded in EXCLUDED_DOMAINS):
                                continue
                            seen_domains.add(domain)
                            candidates.append(CandidateDomain(
                                title=title,
                                url=video_url,
                                domain=domain,
                                post_date=post_date,
                                upvote_count=0,
                                comment_count=0,
                                source="youtube"
                            ))
                    except Exception:
                        pass
        except Exception as e:
            print(f"YouTube Scraper Error: {e}")

    print(f"SUCCESS: YouTube Scraper finished! Returning {len(candidates)} domains.")
    return candidates

if __name__ == "__main__":
    import asyncio
    async def main():
        domains = await get_youtube_urls()
        for d in domains:
            print(d)
    asyncio.run(main())