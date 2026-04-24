# Viral Domain Arbitrage Finder

A full-stack application that automates the discovery of domains from once-viral consumer products (2014-2019) that have since lapsed in registration. The tool scores domains by opportunity value, checks for trademark risk, and presents results in a filterable dashboard UI.

## 🎯 Purpose

This tool helps domain investors and entrepreneurs identify valuable expired domains that were once associated with viral products. By analyzing historical data from Reddit, Hacker News, and Product Hunt, combined with domain authority metrics and trademark checks, it surfaces high-opportunity domains for potential acquisition.

## ⚠️ Legal Disclaimer

**IMPORTANT**: This tool is for research and educational purposes only.

- Always conduct thorough due diligence before purchasing any domain
- Verify trademark status independently using official USPTO databases
- Respect intellectual property rights and trademark laws
- Domain availability information may be outdated - always verify with a registrar
- The authors are not responsible for any legal issues arising from domain purchases
- Consult with a legal professional before making significant domain investments

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **Scrapers**: Collect viral product mentions from Reddit, Hacker News, Product Hunt, and ExpiredDomains.net
- **Enrichment**: WHOIS lookups, Wayback Machine analysis, domain authority checks, trademark screening
- **Scoring Engine**: Calculates composite opportunity scores based on multiple metrics
- **REST API**: FastAPI endpoints for job management, results retrieval, and CSV export

### Frontend (React/Vite)
- Modern React UI with TanStack Table for data visualization
- Real-time job progress tracking
- Advanced filtering and sorting capabilities
- Responsive design

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional, for containerized deployment)

## 🔑 API Keys Required

### Product Hunt API (Optional, for Product Hunt scraping)
1. Go to https://api.producthunt.com/v2/docs
2. Create a developer account
3. Generate an API token
4. Note: This is optional - the tool works without it using Reddit and Hacker News only

**No other API keys required!** The tool uses:
- Reddit data via the public Pushshift API (no auth needed)
- Hacker News via the public Algolia API (no auth needed)
- Wayback Machine via Archive.org's public API (no auth needed)

## ⚙️ Installation

### Option 1: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API keys
cp ../.env.example .env
# Edit .env and add your actual API keys
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp ../.env.example .env
```

### Option 2: Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🚀 Usage

### Starting the Application

#### Local Development

**Backend:**
```bash
cd backend
python main.py
# API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Frontend:**
```bash
cd frontend
npm run dev
# UI will be available at http://localhost:5173
```

#### Docker

```bash
docker-compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Using the API

#### 1. Start a Scan

```bash
curl -X POST http://localhost:8000/api/scan/start \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["reddit", "hackernews", "producthunt"]
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "estimated_time_seconds": 300
}
```

#### 2. Check Scan Status

```bash
curl http://localhost:8000/api/scan/status/{job_id}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress_percent": 65,
  "domains_found": 342,
  "domains_analyzed": 223,
  "current_phase": "enriching"
}
```

#### 3. Get Results

```bash
curl "http://localhost:8000/api/scan/results/{job_id}?page=1&page_size=25&tier=Gold,Silver"
```

#### 4. Export to CSV

```bash
curl http://localhost:8000/api/scan/results/{job_id}/export -o results.csv
```

#### 5. Get Domain Details

```bash
curl http://localhost:8000/api/domain/{domain}/detail
```

#### 6. Refresh Domain Data

```bash
curl http://localhost:8000/api/domain/{domain}/refresh
```

## 📊 Opportunity Score Explanation

The **Opportunity Score** is a composite metric (0-100) calculated from:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Domain Age** | 10% | Older domains generally have more SEO value |
| **Backlinks** | 20% | Number of quality backlinks pointing to the domain |
| **Alexa Rank** | 10% | Historical traffic ranking (if available) |
| **Wayback Snapshots** | 15% | Number of archived versions (indicates site activity) |
| **E-commerce Indicators** | 15% | Presence of shopping/product keywords in archived content |
| **Domain Authority** | 20% | Moz DA score (0-100) |
| **Trademark Risk** | -10% | Penalty if potential trademark conflicts detected |

### Tier Classification

- **Gold** (Score ≥ 70): High-opportunity domains with strong metrics
- **Silver** (Score 50-69): Good potential with moderate metrics
- **Bronze** (Score < 50): Lower opportunity or incomplete data

## 🗂️ Project Structure

```
viral-domain-finder/
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── config.py                    # Configuration and constants
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Backend container config
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── reddit_scraper.py        # Reddit/Pushshift API
│   │   ├── hackernews_scraper.py    # Hacker News Algolia API
│   │   ├── producthunt_scraper.py   # Product Hunt GraphQL API
│   │   └── expired_domains_scraper.py
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── whois_checker.py         # Domain availability checks
│   │   ├── wayback_checker.py       # Archive.org analysis
│   │   ├── authority_checker.py     # Moz DA/PA metrics
│   │   └── trademark_checker.py     # USPTO screening
│   ├── scoring/
│   │   ├── __init__.py
│   │   └── opportunity_scorer.py    # Composite scoring algorithm
│   └── models/
│       ├── __init__.py
│       └── domain_result.py         # Pydantic data models
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile                   # Frontend container config
│   └── src/
│       ├── App.jsx                  # Main application component
│       ├── main.jsx                 # Entry point
│       ├── components/
│       │   ├── DomainTable.jsx      # TanStack Table implementation
│       │   ├── FilterBar.jsx        # Search and filter controls
│       │   ├── ScoreBadge.jsx       # Score visualization
│       │   ├── DomainDetailModal.jsx
│       │   └── ExportButton.jsx
│       └── api/
│           └── client.js            # API wrapper
├── docker-compose.yml               # Multi-container orchestration
├── .env.example                     # Environment variables template
└── README.md                        # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root (optional):

```env
# Product Hunt API (Optional)
PRODUCTHUNT_API_TOKEN=your_producthunt_token

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

**Note:** The tool works without any API keys! Product Hunt API is optional for additional data sources.

### Adjusting Scoring Weights

Edit `backend/config.py` to customize the scoring algorithm:

```python
SCORING_WEIGHTS = {
    "domain_age": 0.1,
    "backlinks": 0.2,
    "alexa_rank": 0.1,
    "wayback_snapshots": 0.15,
    "ecommerce_indicators": 0.15,
    "domain_authority": 0.2,
    "trademark_risk": -0.1
}
```

### Rate Limiting

Adjust concurrent requests and delays in `backend/config.py`:

```python
MAX_CONCURRENT_REQUESTS = 10
REQUEST_DELAY_SECONDS = 1.5
```

## 🐛 Troubleshooting

### Common Issues

**WHOIS Lookups Failing**
- Some WHOIS servers have rate limits
- Solution: Reduce `MAX_CONCURRENT_REQUESTS` in config.py

**Reddit API Errors**
- Verify your client ID and secret are correct
- Ensure you're using the correct app type (script)

**Wayback Machine Timeouts**
- Archive.org can be slow during peak times
- The tool implements retry logic with exponential backoff

**Product Hunt API Quota Exceeded**
- Free tier has daily limits
- Consider upgrading or spreading scans over multiple days

## 📈 Performance Tips

1. **Start with smaller scopes**: Test with a single source before running all scrapers
2. **Use caching**: Results are cached for 24 hours to avoid redundant API calls
3. **Filter early**: Adjust availability filters to reduce enrichment workload
4. **Monitor rate limits**: Watch API response headers for rate limit warnings

## 🤝 Contributing

This is a research tool. If you'd like to contribute:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📝 License

This project is provided as-is for educational and research purposes. See LICENSE file for details.

## ⚖️ Ethics & Best Practices

1. **Respect robots.txt**: The scrapers follow rate limiting best practices
2. **API terms of service**: Ensure your usage complies with Reddit, Product Hunt, and Moz ToS
3. **Trademark respect**: Never purchase domains that infringe on active trademarks
4. **Domain squatting**: Use this tool for legitimate business purposes, not cybersquatting
5. **Privacy**: Do not scrape or store personal information

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Review existing documentation
- Check API provider status pages if experiencing connectivity issues

# ViralFinder
>>>>>>> origin/main
## 🔄 Updates & Roadmap

Future improvements may include:
- Database persistence for scan results
- Email notifications for completed scans
- Integration with domain registrars for instant purchase
- ML-based scoring improvements
- Additional data sources (Twitter, GitHub trending)
- Bulk domain checking

---

**Remember**: This tool is for research and educational purposes. Always conduct thorough due diligence and consult legal professionals before making domain investment decisions.
=======
# ViralFinder
>>>>>>> origin/main
