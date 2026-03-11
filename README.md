# AI Job Scraper

A scalable Python pipeline that discovers companies using modern Applicant Tracking Systems (ATS) and scrapes job postings for AI, ML, and Data roles.

The system continuously expands coverage by discovering new companies using ATS platforms and scraping their job boards.

---

# Overview

This project builds a **self-expanding job discovery and scraping system**.

The pipeline:

1. Discovers companies using different ATS platforms
2. Scrapes job boards in parallel
3. Filters relevant roles
4. Deduplicates results
5. Removes previously seen jobs
6. Outputs only **new jobs**

---

# System Architecture

```
ATS Discovery
    │
    ▼
ATS Company Lists
(data/{ats}_companies.txt)
    │
    ▼
Parallel Scrapers
(Greenhouse • Lever • Workday • Ashby • Workable • Jobvite • SmartRecruiters)
    │
    ▼
Raw Job Collection
    │
    ▼
Filtering Pipeline
(title • location • freshness)
    │
    ▼
Deduplication Engine
    │
    ▼
Seen Job Cache
(job_cache.json)
    │
    ▼
New Jobs Output
(console • Google Sheets)
```

---

# Supported ATS Platforms

| ATS             | Discovery | Scraping |
| --------------- | --------- | -------- |
| Greenhouse      | ✓         | ✓        |
| Lever           | ✓         | ✓        |
| Workday         | ✓         | ✓        |
| Ashby           | ✓         | ✓        |
| Workable        | ✓         | ✓        |
| Jobvite         | ✓         | ✓        |
| SmartRecruiters | ✓         | ✓        |

Each ATS has a **dedicated scraper module** for reliability.

---

# Project Structure

```
src/
│
├── pipeline/
│   ├── collector.py
│   ├── discovery_stage.py
│   ├── job_filter.py
│   ├── dedupe.py
│   ├── excel_writer.py
│   └── scheduler.py
│
├── scrapers/
│   ├── greenhouse_scraper.py
│   ├── lever_scraper.py
│   ├── workday_scraper.py
│   ├── ashby_scraper.py
│   ├── workable_scraper.py
│   ├── jobvite_scraper.py
│   └── smartrecruiters_scraper.py
│
├── discovery/
│   ├── ats_detector.py
│   ├── career_ats_detector.py
│   ├── ats_network_discovery.py
│   ├── smartrecruiters_discovery.py
│   ├── learned_companies.py
│   ├── persist_discovered.py
│   ├── save_companies.py
│   └── crawl_scheduler.py
│
├── utils/
│   ├── logging.py
│   ├── log_sections.py
│   ├── job_cache.py
│   ├── http_retry.py
│   ├── file_loader.py
│   ├── location_cleaner.py
│   ├── url_normalizer.py
│   ├── posted_at_utils.py
│   ├── html_timestamp_extractor.py
│   └── time_utils.py
│
└── config/
    ├── consts.py
    ├── settings.py
    └── search_queries.py
```

---

# Discovery System

Discovery automatically finds companies using ATS platforms.

Entry point:

```
src/pipeline/discovery_stage.py
```

Discovery sources include:

### Domain ATS Detection

Detects ATS usage by scanning company domains.

Example:

```
company.com → career page → greenhouse
```

Handled by:

```
src/discovery/ats_detector.py
```

---

### Career Page Detection

Analyzes career pages directly to identify ATS providers.

```
src/discovery/career_ats_detector.py
```

---

### ATS Network Discovery

Some ATS boards reference other companies using the same ATS.

Example:

```
Greenhouse board → discover other greenhouse companies
```

Handled by:

```
src/discovery/ats_network_discovery.py
```

---

### SmartRecruiters Global Feed

SmartRecruiters exposes a global search API:

```
https://jobs.smartrecruiters.com/sr-jobs/search
```

Used to discover company identifiers.

Handled by:

```
src/discovery/smartrecruiters_discovery.py
```

---

### Learned Company Expansion

When scraping jobs, new companies can be discovered from job URLs.

These are automatically persisted.

```
src/discovery/learned_companies.py
```

---

# Company Storage

Discovered companies are stored in:

```
data/{ats}_companies.txt
```

Example:

```
data/
├── greenhouse_companies.txt
├── lever_companies.txt
├── workday_companies.txt
├── ashby_companies.txt
├── workable_companies.txt
├── jobvite_companies.txt
└── smartrecruiters_companies.txt
```

---

# Scraping Pipeline

Main orchestrator:

```
src/pipeline/collector.py
```

Scrapers run **in parallel** using:

```
ThreadPoolExecutor
```

Pipeline flow:

```
load company lists
    ↓
run ATS scrapers in parallel
    ↓
collect raw jobs
    ↓
filter jobs
    ↓
dedupe jobs
    ↓
remove cached jobs
    ↓
return new jobs
```

---

# Job Filtering

Implemented in:

```
src/pipeline/job_filter.py
```

Filtering rules include:

### Title Filtering

Target roles include:

* Data Scientist
* Senior Data Scientist
* Data Analyst
* Machine Learning Engineer
* AI Engineer
* Applied Scientist

Configured in:

```
src/config/search_queries.py
```

---

### Location Filtering

Location normalization handled by:

```
src/utils/location_cleaner.py
```

Supports:

* city
* state
* country
* remote roles

---

### Freshness Filtering

Jobs older than a configured window are filtered out.

Timestamp utilities:

```
posted_at_utils.py
html_timestamp_extractor.py
workday_timestamp.py
```

---

# Deduplication

Handled in:

```
src/pipeline/dedupe.py
```

Removes duplicates caused by:

* multiple ATS sources
* multiple company boards
* identical job listings

Typical dedupe key:

```
title + company + location
```

---

# Job Cache

To avoid repeating jobs across runs, the system stores previously seen jobs.

```
src/utils/job_cache.py
```

This ensures only **new jobs are returned each run**.

---

# Logging

Logging utilities:

```
src/utils/logging.py
src/utils/log_sections.py
```

Log sections include:

```
ATS DISCOVERY
SCRAPER RESULTS
FILTER PIPELINE
DEDUPLICATION
CACHE FILTER
```

---

# Exporting Jobs

Jobs can be exported to **Google Sheets**.

```
src/pipeline/excel_writer.py
```

Uses:

```
gspread
```

---

# Installation

Clone the repository:

```
git clone <repo>
cd job-scraper
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# Running the Pipeline

Run the full pipeline:

```
python main.py
```

Typical run flow:

```
ATS discovery
company list update
parallel scraping
job filtering
deduplication
cache filtering
new jobs output
```

---

# Scheduling

Run the scraper daily using cron:

```
0 10 * * * python main.py
```

Runs every day at **10 AM**.

---

# Development Notes

Do not commit:

```
venv/
__pycache__/
*.pyc
*.json credentials
```

Use `.gitignore`.

---

# Future Improvements

Potential enhancements:

### Discovery

* LinkedIn company discovery
* sitemap parsing
* domain expansion

### Scraping

* async scraping
* proxy rotation
* rate limiting

### Filtering

* semantic job classification
* ML-based relevance scoring

### Deduplication

* fuzzy job matching
* cross-ATS duplicate detection

---

If you want, I can also show you **how to make this README look *much* more professional on GitHub** (like top engineering repos) by adding:

• badges
• collapsible sections
• centered architecture diagrams
• screenshots of scraper logs
• repo stats

It will make the repo look **10x more polished**.
