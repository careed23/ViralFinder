import os
from dotenv import load_dotenv
load_dotenv()

# Date Ranges
SCAN_DATE_FROM = os.getenv("SCAN_DATE_FROM", "2014-01-01")
SCAN_DATE_TO = os.getenv("SCAN_DATE_TO", "2022-12-31")

# Viral Subreddits for Reddit Scraper
VIRAL_SUBREDDITS = [
    "shutdownreddits", "entrepreneur", "startups", 
    "SomebodyMakeThis", "AppStore", "ProductHunters"
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

# Scoring Weights
SCORING_WEIGHTS = {
    "estimated_traffic": 0.30,   # Using wayback snapshot count as a proxy
    "backlinks": 0.25,
    "ecommerce_indicators": 0.20,
    "domain_authority": 0.10,
    "domain_age": 0.08,
    "alexa_rank": 0.00,          # Deprecated
    "trademark_risk": -0.10,
    "ai_confirmed_product": 0.07,
}

# Request Limits
MAX_CONCURRENT_REQUESTS = 10
REQUEST_DELAY_SECONDS = 5.0

# Excluded Domains (social platforms, news sites, etc.)
EXCLUDED_DOMAINS = [
    "youtube.com", "twitter.com", "facebook.com", "instagram.com",
    "reddit.com", "medium.com", "techcrunch.com", "thenextweb.com",
    "mashable.com", "cnn.com", "bbc.com", "nytimes.com", "amazon.com",
    "ebay.com", "walmart.com", "target.com", "apple.com", "google.com",
    "microsoft.com", "wikipedia.org"
]
