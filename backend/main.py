import asyncio
import uuid
import logging
import pandas as pd
import traceback  # Added for better debugging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import io

from database import init_db, persist_scan_results, get_scan_results_from_db
from config import MAX_CONCURRENT_REQUESTS
from models.domain_result import DomainResult
from scrapers.hackernews_scraper import get_hackernews_posts
from scrapers.producthunt_scraper import get_producthunt_posts
from scrapers.reddit_scraper import get_reddit_posts
from scrapers.youtube_scraper import get_youtube_urls
from enrichment.whois_checker import check_whois
from enrichment.wayback_checker import check_wayback_machine
from enrichment.authority_checker import check_domain_authority
from enrichment.trademark_checker import check_trademark_risk
from scoring.opportunity_scorer import calculate_opportunity_score

# Standard logging configuration
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Viral Domain Arbitrage Finder API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: Dict[str, Dict[str, Any]] = {}

class ScanRequest(BaseModel):
    sources: List[str] = Field(..., min_items=1, description="List of sources to scan")

class ScanResponse(BaseModel):
    job_id: str
    status: str
    estimated_time_seconds: int

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/api/scan/start", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress_percent": 0,
        "domains_found": 0,
        "domains_analyzed": 0,
        "current_phase": "starting",
        "results": [],
        "created_at": datetime.utcnow()
    }
    background_tasks.add_task(run_scan_job, job_id, request.sources)
    return ScanResponse(job_id=job_id, status="started", estimated_time_seconds=300)

@app.get("/api/scan/status/{job_id}")
async def get_scan_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress_percent": job["progress_percent"],
        "domains_found": job["domains_found"],
        "domains_analyzed": job["domains_analyzed"],
        "current_phase": job["current_phase"],
        "error": job.get("error")
    }

@app.get("/api/scan/results/{job_id}")
async def get_scan_results(job_id: str, page: int = 1, page_size: int = 25):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if jobs[job_id]["status"] == "completed":
        results = get_scan_results_from_db(job_id)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "total": len(results),
            "page": page,
            "page_size": page_size,
            "results": results[start:end]
        }
    else:
        results = jobs[job_id].get("results", [])
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "total": len(results),
            "page": page,
            "page_size": page_size,
            "results": [r.dict() for r in results[start:end]]
        }

async def run_scan_job(job_id: str, sources: List[str]):
    jobs[job_id]["status"] = "running"
    jobs[job_id]["current_phase"] = "scraping"
    jobs[job_id]["progress_percent"] = 5
    
    try:
        scraping_tasks = []
        if "hackernews" in sources: scraping_tasks.append(get_hackernews_posts())
        if "producthunt" in sources: scraping_tasks.append(get_producthunt_posts())
        if "reddit" in sources: scraping_tasks.append(get_reddit_posts())
        if "youtube" in sources: scraping_tasks.append(get_youtube_urls())
        
        scraping_results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
        
        all_candidates = []
        for res in scraping_results:
            if isinstance(res, list):
                all_candidates.extend(res)
        
        domain_map: Dict[str, Any] = {}
        for candidate in all_candidates:
            domain = candidate.domain if hasattr(candidate, "domain") else str(candidate)
            if domain and domain not in domain_map:
                domain_map[domain] = candidate
        
        jobs[job_id]["domains_found"] = len(domain_map)
        jobs[job_id]["progress_percent"] = 30
        jobs[job_id]["current_phase"] = "enriching"
        
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        async def enrich_domain(domain):
            async with semaphore:
                try:
                    whois_result = await check_whois(domain)
                    if not whois_result or whois_result.expiry_status not in ["AVAILABLE", "EXPIRING_SOON"]:
                        return None
                    
                    wayback_result = await check_wayback_machine(domain)
                    authority_result = await check_domain_authority(domain)
                    trademark_result = await check_trademark_risk(domain)
                    
                    score_result = await calculate_opportunity_score(
                        domain, whois_result, wayback_result, authority_result, trademark_result, {}
                    )
                    
                    score = score_result.score
                    tier = "Gold" if score >= 0.7 else "Silver" if score >= 0.5 else "Bronze"
                    
                    # THE FIX: Bulletproof sanitization before creating the DomainResult object
                    return DomainResult(
                        domain=domain,
                        opportunity_score=score,
                        tier=tier,
                        ai_category="Uncategorized",
                        is_available=getattr(whois_result, 'is_available', False) or False,
                        expiry_status=getattr(whois_result, 'expiry_status', "UNKNOWN") or "UNKNOWN",
                        registrar=getattr(whois_result, 'registrar', "N/A") or "N/A",
                        creation_date=getattr(whois_result, 'creation_date', None),
                        expiration_date=getattr(whois_result, 'expiration_date', None),
                        last_updated=getattr(whois_result, 'last_updated', None),
                        whois_status=getattr(whois_result, 'status', "N/A") or "N/A",
                        total_snapshots=int(getattr(wayback_result, 'total_snapshots', 0) or 0),
                        peak_activity_year=int(getattr(wayback_result, 'peak_activity_year', 0) or 0),
                        first_snapshot_date=getattr(wayback_result, 'first_snapshot_date', None),
                        last_snapshot_date=getattr(wayback_result, 'last_snapshot_date', None),
                        is_product_site=bool(getattr(wayback_result, 'is_product_site', False)),
                        has_product_signals=bool(getattr(wayback_result, 'is_product_site', False)),
                        page_title=getattr(wayback_result, 'page_title', "") or "",
                        meta_description=getattr(wayback_result, 'meta_description', "") or "",
                        domain_authority=int(getattr(authority_result, 'domain_authority', 0) or 0),
                        page_authority=int(getattr(authority_result, 'page_authority', 0) or 0),
                        linking_root_domains=int(getattr(authority_result, 'linking_root_domains', 0) or 0),
                        total_links=int(getattr(authority_result, 'total_links', 0) or 0),
                        has_trademark_risk=bool(getattr(trademark_result, 'has_trademark_risk', False)) if trademark_result else False,
                        trademark_details=getattr(trademark_result, 'details', "N/A") if trademark_result else "N/A",
                        sources=[domain_map[domain].source] if hasattr(domain_map[domain], 'source') else []
                    )
                except Exception as e:
                    logging.error(f"Error enriching domain {domain}: {e}")
                    return None

        enrichment_tasks = [asyncio.create_task(enrich_domain(d)) for d in domain_map.keys()]
        enriched = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
        
        enriched_results = [r for r in enriched if isinstance(r, DomainResult)]
        
        # Sort results
        enriched_results.sort(key=lambda x: x.opportunity_score or 0, reverse=True)
        
        jobs[job_id]["results"] = enriched_results
        jobs[job_id]["domains_analyzed"] = len(enriched_results)
        
        persist_scan_results(job_id, enriched_results)

        jobs[job_id]["progress_percent"] = 100
        jobs[job_id]["current_phase"] = "completed"
        jobs[job_id]["status"] = "completed"
        
    except Exception as e:
        logging.error(f"Critical Error in scan job {job_id}: {e}")
        traceback.print_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["current_phase"] = "failed"

@app.get("/api/scan/results/{job_id}/export")
async def export_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    results = jobs[job_id].get("results", [])
    if not results:
        raise HTTPException(status_code=400, detail="No results to export")
    
    df = pd.DataFrame([r.dict() for r in results])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Domain Results')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=domain_results_{job_id}.xlsx"}
    )