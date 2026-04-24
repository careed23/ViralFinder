import os

# Product Hunt API
PRODUCTHUNT_API_TOKEN = os.getenv("PRODUCTHUNT_API_TOKEN")

# Date Ranges
DATE_RANGE_START = "2014-01-01"
DATE_RANGE_END = "2019-12-31"

# Viral Subreddits for Reddit Scraper
VIRAL_SUBREDDITS = [
    "shutupandtakemymoney", "buyitforlife", "gadgets",
    "entrepreneur", "startups", "InternetIsBeautiful", "technology",
    "ProductHunter", "SideProject", "passive_income", "ecommerce"
]

# Product Hunt Topics
PRODUCTHUNT_TOPICS = [
    "Productivity", "E-Commerce", "Consumer",
    "Gadgets", "Health", "Fitness", "Food", "Lifestyle", "Shopping"
]

# ExpiredDomains.net Product Keywords
PRODUCT_KEYWORDS = [
    "shop", "kit", "gear", "hub", "lab", "tech", "box", "co", "io",
    "app", "pro", "plus", "go", "now", "get", "try", "my", "us"
]

# Scoring Weights (Wayback Machine focused - no Moz API)
SCORING_WEIGHTS = {
    "domain_age": 0.15,
    "wayback_snapshots": 0.35,
    "ecommerce_indicators": 0.25,
    "peak_activity": 0.15,
    "trademark_risk": -0.1
}

# Request Limits
MAX_CONCURRENT_REQUESTS = 10
REQUEST_DELAY_SECONDS = 1.5

# Excluded Domains (social platforms, news sites, etc.)
EXCLUDED_DOMAINS = [
    "youtube.com", "twitter.com", "facebook.com", "instagram.com",
    "reddit.com", "medium.com", "techcrunch.com", "thenextweb.com",
    "mashable.com", "cnn.com", "bbc.com", "nytimes.com", "amazon.com",
    "ebay.com", "walmart.com", "target.com", "apple.com", "google.com",
    "microsoft.com", "wikipedia.org"
]
