from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CandidateDomain(BaseModel):
    domain: str
    title: Optional[str] = None
    url: Optional[str] = None
    post_date: Optional[datetime] = None
    upvote_count: Optional[int] = None
    comment_count: Optional[int] = None
    source: Optional[str] = None
    subreddit: Optional[str] = None
    permalink: Optional[str] = None
    topics: Optional[List[str]] = Field(default_factory=list)
    domain_age: Optional[int] = None
    backlinks_count: Optional[int] = None
    alexa_rank: Optional[int] = None
    available_status: Optional[str] = None


class DomainResult(BaseModel):
    domain: str
    opportunity_score: Optional[float] = None
    tier: Optional[str] = None  # e.g., "Gold", "Silver", "Bronze"
    
    # WHOIS Data
    is_available: Optional[bool] = None
    expiry_status: Optional[str] = None  # AVAILABLE, EXPIRING_SOON, TAKEN, UNKNOWN
    registrar: Optional[str] = None
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    whois_status: Optional[str] = None
    
    # Wayback Machine Data
    total_snapshots: Optional[int] = None
    peak_activity_year: Optional[int] = None
    first_snapshot_date: Optional[datetime] = None
    last_snapshot_date: Optional[datetime] = None
    is_product_site: Optional[bool] = None
    page_title: Optional[str] = None
    meta_description: Optional[str] = None
    
    # Authority Data
    domain_authority: Optional[int] = None
    page_authority: Optional[int] = None
    linking_root_domains: Optional[int] = None
    total_links: Optional[int] = None
    
    # Trademark Data
    has_trademark_risk: Optional[bool] = None
    trademark_details: Optional[str] = None
    
    # Source/Origin Data
    sources: Optional[List[str]] = Field(default_factory=list)
    viral_posts: Optional[List[dict]] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
