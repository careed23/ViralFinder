import asyncio
import uuid
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

from config import MAX_CONCURRENT_REQUESTS
from models.domain_result import DomainResult
from scrapers.hackernews_scraper import get_hackernews_posts
from scrapers.producthunt_scraper import get_producthunt_posts
from enrichment.whois_checker import check_whois
from enrichment.wayback_checker import check_wayback_machine
from enrichment.authority_checker import check_domain_authority
from enrichment.trademark_checker import check_trademark_risk
from scoring.opportunity_scorer import calculate_opportunity_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Viral Domain Arbitrage Finder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: Dict[str, Dict[str, Any]] = {}

class ScanConfig(BaseModel):
    sources: List[str] = ["hackernews", "producthunt"]

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/api/scan/start")
async def start_scan(config: ScanConfig, background_tasks: BackgroundTasks):
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
    background_tasks.add_task(run_scan_job, job_id, config)
    return {"job_id": job_id, "status": "started", "estimated_time_seconds": 300}

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
    results = jobs[job_id].get("results", [])
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "total": len(results),
        "page": page,
        "page_size": page_size,
        "results": [r.dict() for r in results[start:end]]
    }

async def run_scan_job(job_id: str, config: ScanConfig):
    jobs[job_id]["status"] = "running"
    jobs[job_id]["current_phase"] = "scraping"
    jobs[job_id]["progress_percent"] = 5
    try:
        scraping_tasks = []
        if "hackernews" in config.sources:
            scraping_tasks.append(get_hackernews_posts())
        if "producthunt" in config.sources:
            scraping_tasks.append(get_producthunt_posts())
        results = await asyncio.gather(*scraping_tasks, return_exceptions=True)
        all_candidates = []
        for result in results:
            if isinstance(result, list):
                all_candidates.extend(result)
        domain_map: Dict[str, Any] = {}
        for candidate in all_candidates:
            domain = candidate.domain if hasattr(candidate, "domain") else str(candidate)
            if domain and domain not in domain_map:
                domain_map[domain] = candidate
        jobs[job_id]["domains_found"] = len(domain_map)
        jobs[job_id]["progress_percent"] = 30
        jobs[job_id]["current_phase"] = "enriching"
        enriched_results = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        async def enrich_domain(domain):
            async with semaphore:
                try:
                    whois_result = await check_whois(domain)
                    if whois_result.expiry_status not in ["AVAILABLE", "EXPIRING_SOON"]:
                        return None
                    wayback_result = await check_wayback_machine(domain)
                    authority_result = await check_domain_authority(domain)
                    trademark_result = await check_trademark_risk(domain)
                    score_result = await calculate_opportunity_score(
                        domain, whois_result, wayback_result, authority_result, trademark_result
                    )
                    score = score_result.score
                    tier = "Gold" if score >= 0.7 else "Silver" if score >= 0.5 else "Bronze"
                    return DomainResult(
                        domain=domain,
                        opportunity_score=score,
                        tier=tier,
                        is_available=whois_result.is_available,
                        expiry_status=whois_result.expiry_status,
                        registrar=whois_result.registrar,
                        creation_date=whois_result.creation_date,
                        expiration_date=whois_result.expiration_date,
                        last_updated=whois_result.last_updated,
                        whois_status=whois_result.whois_status,
                        total_snapshots=wayback_result.total_snapshots,
                        peak_activity_year=wayback_result.peak_activity_year,
                        first_snapshot_date=wayback_result.first_snapshot_date,
                        last_snapshot_date=wayback_result.last_snapshot_date,
                        is_product_site=wayback_result.is_product_site,
                        page_title=wayback_result.page_title,
                        meta_description=wayback_result.meta_description,
                        domain_authority=authority_result.domain_authority,
                        page_authority=authority_result.page_authority,
                        linking_root_domains=authority_result.linking_root_domains,
                        total_links=authority_result.total_links,
                        has_trademark_risk=trademark_result.has_risk,
                        trademark_details=trademark_result.details,
                        sources=[domain_map[domain].source] if hasattr(domain_map[domain], 'source') else []
                    )
                except Exception as e:
                    logger.error(f"Error enriching domain {domain}: {e}")
                    return None

        enrichment_tasks = [enrich_domain(d) for d in domain_map.keys()]
        enriched = await asyncio.gather(*enrichment_tasks)
        enriched_results = [r for r in enriched if r is not None]
        
        # Sort by opportunity score
        enriched_results.sort(key=lambda x: x.opportunity_score or 0, reverse=True)
        
        jobs[job_id]["results"] = enriched_results
        jobs[job_id]["domains_analyzed"] = len(enriched_results)
        jobs[job_id]["progress_percent"] = 100
        jobs[job_id]["current_phase"] = "completed"
        jobs[job_id]["status"] = "completed"
        
    except Exception as e:
        logger.error(f"Error in scan job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["progress_percent"] = 100
        jobs[job_id]["current_phase"] = "failed"

@app.get("/api/scan/export/{job_id}")
async def export_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    results = jobs[job_id].get("results", [])
    if not results:
        raise HTTPException(status_code=400, detail="No results to export")
    
    # Convert to DataFrame
    df = pd.DataFrame([r.dict() for r in results])
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Domain Results')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=domain_results_{job_id}.xlsx"}
    )
