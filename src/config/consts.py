import re
import pycountry

# ============================================================
# TITLE FILTERING / TITLE NORMALIZATION
# ============================================================

TITLE_INCLUDE_PATTERNS = [
    r"data scientist",
    r"machine learning engineer",
    r"\bml engineer\b",
    r"ai engineer",
    r"applied scientist",
    r"research scientist",
    r"data analyst",
    r"decision scientist",
    r"ml scientist",
    r"analytics engineer",
    r"deep learning engineer",
    r"nlp engineer",
    r"\bgenai\b",
]

TITLE_EXCLUDE_PATTERNS = [
    r"director",
    r"vp",
    r"vice president",
    r"manager",
    r"intern",
    r"student",
    r"principal architect",
    r"lead",
    r"staff",
    r"principal",
    r"architect",
]

TITLE_CANONICAL = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "eng": "engineer",
    "sr": "senior",
    "jr": "junior",
}

TITLE_INCLUDE_REGEX = [re.compile(p, re.I) for p in TITLE_INCLUDE_PATTERNS]
TITLE_EXCLUDE_REGEX = [re.compile(p, re.I) for p in TITLE_EXCLUDE_PATTERNS]

PUNCT_REGEX = re.compile(r"[^\w\s]")
ROMAN_SUFFIX_REGEX = re.compile(r"\s+(i|ii|iii|iv|v)$")
WHITESPACE_REGEX = re.compile(r"\s+")
TOKEN_SPLIT_REGEX = re.compile(r"[,\-\s]+")

COMPANY_SUFFIXES = [
    "inc", "inc.", "llc", "l.l.c", "corp", "corporation",
    "co", "company", "ltd", "limited", "plc",
]

# ============================================================
# LOCATION / COUNTRY FILTERING
# ============================================================

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}

US_STATE_NAMES = {
    "ALABAMA", "ALASKA", "ARIZONA", "ARKANSAS", "CALIFORNIA", "COLORADO",
    "CONNECTICUT", "DELAWARE", "FLORIDA", "GEORGIA", "HAWAII", "IDAHO",
    "ILLINOIS", "INDIANA", "IOWA", "KANSAS", "KENTUCKY", "LOUISIANA",
    "MAINE", "MARYLAND", "MASSACHUSETTS", "MICHIGAN", "MINNESOTA",
    "MISSISSIPPI", "MISSOURI", "MONTANA", "NEBRASKA", "NEVADA",
    "NEW HAMPSHIRE", "NEW JERSEY", "NEW MEXICO", "NEW YORK",
    "NORTH CAROLINA", "NORTH DAKOTA", "OHIO", "OKLAHOMA", "OREGON",
    "PENNSYLVANIA", "RHODE ISLAND", "SOUTH CAROLINA", "SOUTH DAKOTA",
    "TENNESSEE", "TEXAS", "UTAH", "VERMONT", "VIRGINIA", "WASHINGTON",
    "WEST VIRGINIA", "WISCONSIN", "WYOMING",
}

MAJOR_US_CITIES = {
    "NEW YORK",
    "SAN FRANCISCO",
    "SEATTLE",
    "AUSTIN",
    "BOSTON",
    "CHICAGO",
    "LOS ANGELES",
    "DENVER",
    "ATLANTA",
    "SAN DIEGO",
    "PORTLAND",
    "WASHINGTON",
}

FOREIGN_CITY_BLOCKLIST = {
    "JERUSALEM",
    "TEL AVIV",
    "LONDON",
    "TORONTO",
    "BERLIN",
    "PARIS",
    "AMSTERDAM",
}

ALL_COUNTRIES = {country.name.upper() for country in pycountry.countries}
ALL_COUNTRIES.update({
    "UK",
    "U.K.",
    "UNITED KINGDOM",
    "KOREA",
    "SOUTH KOREA",
    "NORTH KOREA",
})

# ============================================================
# ATS IDENTIFIERS / API ENDPOINTS
# ============================================================

SUPPORTED_ATS = [
    "greenhouse",
    "lever",
    "workday",
    "ashby",
    "workable",
    "jobvite",
]

ATS_WORKDAY = "workday"
ATS_LEVER = "lever"
ATS_JOBVITE = "jobvite"

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{}/jobs"
ASHBY_URL = "https://jobs.ashbyhq.com/api/non-user-graphql"
LEVER_API = "https://api.lever.co/v0/postings"
WORKABLE_V3_API = "https://apply.workable.com/api/v3/accounts/{}/jobs"
WORKABLE_V1_API = "https://apply.workable.com/api/v1/widget/accounts/{}"
WORKABLE_V2_DETAIL_API = "https://apply.workable.com/api/v2/accounts/{}/jobs/{}"
WORKDAY_API_URL_TEMPLATE = "https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
WORKDAY_ORIGIN_TEMPLATE = "https://{host}.myworkdayjobs.com"

JOBVITE_URL_PATTERNS = [
    "https://jobs.jobvite.com/{company}/jobs/alljobs",
    "https://jobs.jobvite.com/{company}/jobs",
]

ASHBY_QUERY = """
query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
  jobBoard: jobBoardWithTeams(
    organizationHostedJobsPageName: $organizationHostedJobsPageName
  ) {
    jobPostings {
      id
      title
      locationName
      workplaceType
      employmentType
    }
  }
}
"""

ASHBY_DETAIL_QUERY = """
query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) {
  jobPosting(
    organizationHostedJobsPageName: $organizationHostedJobsPageName
    jobPostingId: $jobPostingId
  ) {
    id
    title
    publishedDate
  }
}
"""

# ============================================================
# TIMESTAMP / FRESHNESS SETTINGS
# ============================================================

TIMESTAMP_WORKERS = 10
DATE_ONLY_HOUR = 12
FRESHNESS_HOURS = 24

# ============================================================
# ATS DISCOVERY / CAREER PAGE DETECTION
# ============================================================

INVALID_SLUGS = {
    "careers",
    "jobs",
    "job",
    "apply",
    "board",
    "boards",
    "hiring",
    "-----",
    "------",
}

CAREER_PATHS = [
    "/careers",
    "/jobs",
    "/careers/jobs",
    "/about/careers",
    "/careers/openings",
    "/join-us",
    "/work-with-us",
    "/company/careers",
    "/join",
    "/careers.html",
    "/open-roles",
    "/roles",
    "/positions",
    "/opportunities",
    "/hiring",
    "/careers-at",
    "/join-the-team",
]

CAREER_SUBDOMAINS = [
    "careers",
    "jobs",
    "work",
    "join",
    "joinus",
    "careers-us",
    "jobs-us",
    "careers-uk",
    "careers-eu",
    "talent",
    "opportunities",
    "hiring",
    "team",
]

WORKDAY_REGEX = re.compile(
    r"https://[a-zA-Z0-9-]+\.wd[0-9]+\.myworkdayjobs\.com/[a-zA-Z0-9_-]+"
)

ATS_REGEX = {
    "greenhouse": [
        re.compile(r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)", re.I),
        re.compile(r"boards\.greenhouse\.io/embed/job_board.*?for=([a-zA-Z0-9_-]+)", re.I),
    ],
    "lever": [
        re.compile(r"jobs\.lever\.co/([a-zA-Z0-9_-]+)", re.I),
    ],
    "ashby": [
        re.compile(r"jobs\.ashbyhq\.com/([a-zA-Z0-9_-]+)", re.I),
    ],
    "workable": [
        re.compile(r"apply\.workable\.com/([a-zA-Z0-9_-]+)", re.I),
    ],
    "jobvite": [
        re.compile(r"jobs\.jobvite\.com/([a-zA-Z0-9_-]+)", re.I),
    ],
    "workday": [
        re.compile(r"myworkdayjobs\.com/([^/]+)/", re.I),
    ],
    "smartrecruiters": [
        re.compile(r"jobs\.smartrecruiters\.com/([a-zA-Z0-9\-_]+)", re.I),
    ],
}

SITEMAP_PATHS = [
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/sitemap1.xml",
    "/sitemap-careers.xml",
    "/sitemap_jobs.xml",
]

# ============================================================
# SEARCH / GITHUB DISCOVERY
# ============================================================

SEARCH_URL = "https://lite.duckduckgo.com/lite/?q={}&s={}"
GITHUB_SEARCH = "https://api.github.com/search/code?q={}&per_page=100"

ATS_PATTERNS = {
    "greenhouse": re.compile(r"boards\.greenhouse\.io/([a-zA-Z0-9\-]+)"),
    "lever": re.compile(r"jobs\.lever\.co/([a-zA-Z0-9\-]+)"),
    "ashby": re.compile(r"jobs\.ashbyhq\.com/([a-zA-Z0-9\-]+)"),
    "workable": re.compile(r"apply\.workable\.com/([a-zA-Z0-9\-]+)"),
    "jobvite": re.compile(r"jobs\.jobvite\.com/([a-zA-Z0-9\-]+)"),
}

ATS_SITES = {
    "lever": "site:jobs.lever.co",
    "ashby": "site:jobs.ashbyhq.com",
    "workable": "site:apply.workable.com",
    "jobvite": "site:jobs.jobvite.com",
}

SEARCH_JOB_TITLES = [
    "software engineer",
    "data scientist",
    "machine learning engineer",
]

QUERIES = [
    "boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "apply.workable.com",
]

# ============================================================
# VISA SIGNALS
# ============================================================

NEGATIVE_VISA_PATTERNS = [
    r"must be authorized to work",
    r"must have authorization to work",
    r"must be legally authorized to work",
    r"unrestricted work authorization",
    r"no visa sponsorship",
    r"cannot sponsor",
    r"unable to sponsor",
    r"we do not sponsor",
    r"without sponsorship",
    r"not provide visa sponsorship",
    r"authorized to work in the (united states|us|u\.s\.)",
]

POSITIVE_VISA_PATTERNS = [
    r"h-?1b",
    r"visa sponsorship",
    r"sponsor",
    r"work authorization.*provided",
    r"opt",
    r"cpt",
]

# ============================================================
# SKILL NORMALIZATION / DISCOVERY SUPPORT
# ============================================================

NORMALIZATION_MAP = {
    "llm apis": "llm",
    "large language models": "llm",
    "retrievalbased ai systems": "rag",
    "vector databases": "vector db",
    "scikitlearn": "scikit-learn",
    "scikit": "scikit-learn",
    "sklearn": "scikit-learn",
}

DROP_EXACT = {
    "fintech",
    "financial services",
    "payments",
    "phd",
    "models",
    "real-time alerts",
    "data pipelines",
    "llm-based tools",
    "machine learning techniques",
    "noisy, unstructured data",
    "distributed training of ml models",
    "ci/cd pipelines",
}

ALIAS_MAP = {
    "ab testing": "a/b testing",
    "ab tests": "a/b testing",
    "gen ai": "generative ai",
    "claud code": "claude code",
    "air flow": "airflow",
    "regression basics": "regression",
    "machine learning techniques": "machine learning",
}

SQL_FRAGMENT_TERMS = {
    "joins",
    "window functions",
    "ctes",
}

# ============================================================
# QUERY ENGINE
# ============================================================

QUERY_STOPWORDS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "best", "by",
    "engineer", "engineers", "find", "for", "from", "hiring", "in",
    "into", "is", "job", "jobs", "look", "looks", "new", "of", "on",
    "opening", "openings", "opportunity", "opportunities", "or",
    "position", "positions", "requirement", "requirements", "role",
    "roles", "team", "teams", "that", "the", "their", "these", "this",
    "to", "using", "what", "which", "with", "work", "working",
    "strongest", "retrieved", "emphasize", "emphasizes", "focused",
}

# ============================================================
# RESUME EVIDENCE BUILDER
# ============================================================  

COMMON_SKILL_PATTERNS = [
    "python",
    "sql",
    "r",
    "sas",
    "tableau",
    "looker",
    "power bi",
    "excel",
    "airflow",
    "dbt",
    "snowflake",
    "bigquery",
    "databricks",
    "spark",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "machine learning",
    "deep learning",
    "a/b testing",
    "bayesian inference",
    "causal inference",
    "experimental design",
    "hypothesis testing",
    "regression",
    "classification",
    "forecasting",
    "statistical modeling",
    "data science",
    "data analysis",
    "analytics",
    "generative ai",
    "llm",
]

TITLE_PATTERNS = [
    "senior data scientist",
    "research data scientist",
    "staff data scientist",
    "principal data scientist",
    "data scientist",
    "senior data analyst",
    "data analyst",
    "senior machine learning engineer",
    "machine learning engineer",
    "ai engineer",
    "applied scientist",
    "research scientist",
    "analytics engineer",
    "product analyst",
    "business analyst",
    "sr. data scientist",
    "sr. data analyst",
    "data scientist ii",
    "data analyst ii",
    "data analyst i",
    "machine learning intern",
    "machine learning",
]

DOMAIN_SIGNAL_PATTERNS = [
    "fintech",
    "finance",
    "payments",
    "fraud",
    "risk",
    "insurance",
    "healthcare",
    "retail",
    "e-commerce",
    "supply chain",
    "logistics",
    "transportation",
    "media",
    "streaming",
    "advertising",
    "marketplace",
]

ANALYTICS_ML_SIGNAL_PATTERNS = [
    "machine learning",
    "modeling",
    "forecasting",
    "prediction",
    "classification",
    "regression",
    "statistics",
    "statistical",
    "analytics",
    "analysis",
    "data science",
]

EXPERIMENTATION_SIGNAL_PATTERNS = [
    "a/b test",
    "a/b testing",
    "experiment",
    "experimentation",
    "causal inference",
    "bayesian",
    "hypothesis testing",
    "incrementality",
    "quasi-experimental",
    "diff-in-diff",
    "propensity",
    "synthetic control",
]

TOOLING_SIGNAL_PATTERNS = [
    "python",
    "sql",
    "r",
    "sas",
    "tableau",
    "looker",
    "power bi",
    "airflow",
    "dbt",
    "snowflake",
    "bigquery",
    "databricks",
    "spark",
    "pytorch",
    "tensorflow",
]

SECTION_ALIASES = {
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "professional background",
    ],
    "projects": [
        "projects",
        "project experience",
        "relevant projects",
        "academic projects",
    ],
    "education": [
        "education",
        "academic background",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "skills summary",
    ],
}

DATE_PATTERN = re.compile(
    r"(?i)\b("
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}"
    r"|"
    r"\d{4}"
    r")\b"
)

DATE_RANGE_PATTERN = re.compile(
    r"(?i)\b("
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}"
    r"|"
    r"\d{4}"
    r")\b.*\b("
    r"(present|current|now)"
    r"|"
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}"
    r"|"
    r"\d{4}"
    r")\b"
)

ROLE_WORD_HINTS = [
    "scientist",
    "analyst",
    "engineer",
    "intern",
    "manager",
    "consultant",
    "researcher",
    "specialist",
]

SENIORITY_HINTS = [
    "principal",
    "staff",
    "senior",
    "lead",
    "junior",
    "intern",
]

TITLE_NOISE_TOKENS = {
    "a",
    "an",
    "and",
    "for",
    "of",
    "the",
    "jr",
    "junior",
    "sr",
    "senior",
    "lead",
    "staff",
    "principal",
    "ii",
    "iii",
    "iv",
}

_SKILL_ALIASES = {
    "ab testing": "a/b testing",
    "a b testing": "a/b testing",
    "a/b test": "a/b testing",
    "ml": "machine learning",
    "powerbi": "power bi",
    "experiment": "experimentation",
    
}

_ANALYTICS_ML_SIGNAL_CANONICAL = {
    "analysis": "analytics",
    "analytics": "analytics",
    "statistics": "statistics",
    "statistical": "statistics",
}

_ANALYTICS_ML_GENERIC_SIGNALS = {
    "analytics",
    "data science",
}

_SENIORITY_RANKS = {
    "intern": 0,
    "junior": 1,
    "": 2,
    "senior": 3,
    "lead": 4,
    "staff": 4,
    "principal": 5,
}


# ============================================================
# SKILL EXTRACTOR
# ============================================================  

INVALID_SKILL_PATTERNS = [
    r"\bability to\b",
    r"\bstrong\b",
    r"\bexcellent\b",
    r"\bbackground in\b",
    r"\bbackground\b",
    r"\bexperience\b",
    r"\bproficiency\b",
    r"\bskills?\b",
    r"\bcommunication\b",
    r"\bleadership\b",
    r"\bstakeholder\b",
    r"\bbusiness\b",
    r"\bproblem[- ]solving\b",
    r"\bstructured thinking\b",
    r"\battention to detail\b",
    r"\bownership\b",
    r"\bservice\b",
    r"\bperformance\b",
    r"\bdata quality\b",
    r"\bdata integrity\b",
    r"\bdata products?\b",
    r"\bdata pipelines?\b",
    r"\brobust data pipelines?\b",
    r"\bscalable processes?\b",
    r"\bdata models?\b",
    r"\bautomation solutions?\b",
    r"\betl pipelines?\b",
    r"\bdata analysis\b",
    r"\bdata science\b",
    r"\bdata visualization\b",
    r"\bquantitative analysis\b",
    r"\bscripting language\b",
    r"\bsql queries?\b",
    r"\bstatistical techniques\b",
    r"\bml fundamentals\b",
    r"\bbig data experience\b",
    r"\bteaching experience\b",
    r"\badtech\b",
    r"\bctv\b",
    r"\bai capabilities\b",
    r"\bideally\b",
    r"\brigor\b",
    r"\bdevops\b",
    r"\bci/cd practices\b",
    r"\btools\b",
    r"\bdata platforms?\b",
    r"\bscalable data platforms?\b",
]

REQUIRED_CONTEXT_PATTERNS = [
    r"\brequired qualifications\b",
    r"\bminimum qualifications\b",
    r"\bbasic qualifications\b",
    r"\brequirements\b",
    r"\bmust have\b",
    r"\bwhat we're looking for\b",
    r"\bwhat you need\b",
    r"\bwhat you'll need\b",
    r"\bbecause you have\b",
]

PREFERRED_CONTEXT_PATTERNS = [
    r"\bpreferred qualifications\b",
    r"\bbonus points\b",
    r"\bnice to have\b",
    r"\bpreferred\b",
    r"\ba plus\b",
    r"\bis a plus\b",
]

EMBEDDED_SKILL_PATTERNS = [
    (r"\baws athena\b", "aws athena"),
    (r"\bapache spark\b", "apache spark"),
    (r"\bapache beam\b", "apache beam"),
    (r"\bgoogle sheets\b", "google sheets"),
    (r"\binfrastructure as code\b", "infrastructure as code"),
    (r"\bci/cd\b", "ci/cd"),
    (r"\baws\b", "aws"),
    (r"\bsigma\b", "sigma"),
    (r"\btableau\b", "tableau"),
]


# ============================================================
# TAILORING
# ============================================================


CONTEXT_TOKEN_STOPWORDS = {
    "a", "an", "and", "the", "for", "with", "from", "into", "using",
    "senior", "sr", "junior", "jr", "lead", "staff", "principal",
    "data", "analyst", "scientist", "engineer", "manager", "director",
    "product", "platform", "team", "ops", "operation", "operations",
    "ii", "iii", "iv", "i",
}

REWRITE_DIRECTION_PREFIXES = (
    "Lead with",
    "Support with",
    "Keep gap explicit",
    "Do not add",
)