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
    "structured query language sql": "sql",
    "amazon web services aws software": "aws",
    "amazon web services aws cloudformation": "aws cloudformation",
    "amazon dynamodb": "dynamodb",
    "amazon elastic compute cloud ec2": "ec2",
    "amazon redshift": "redshift",
    "apache airflow": "airflow",
    "apache cassandra": "cassandra",
    "apache hadoop": "hadoop",
    "apache hive": "hive",
    "apache kafka": "kafka",
    "apache spark": "spark",
    "atlassian jira": "jira",
    "ibm spss statistics": "spss",
    "ibm terraform": "terraform",
    "microsoft azure software": "azure",
    "microsoft power bi": "power bi",
    "microsoft sql server": "sql server",
    "oracle cloud software": "oracle cloud",
    "oracle java": "java",
    "the mathworks matlab": "matlab",
    "support vector machine": "svm",
    "support vector machines": "svm",
    "random forests": "random forest",
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
    "source control": "version control",
    "source code management": "version control",
    "version control systems": "version control",
    "nlp": "natural language processing",
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
    "aws",
    "azure",
    "azure machine learning",
    "bash",
    "c++",
    "cassandra",
    "couchbase",
    "docker",
    "dynamodb",
    "ec2",
    "hadoop",
    "hive",
    "impala",
    "java",
    "jenkins",
    "jira",
    "kafka",
    "kubernetes",
    "linux",
    "matlab",
    "mongodb",
    "mysql",
    "oracle cloud",
    "redshift",
    "scala",
    "splunk enterprise",
    "spss",
    "sql server",
    "terraform",
    "alteryx",
    "ansible",
    "natural language processing",
    "data mining",
    "data modeling",
    "predictive modeling",
    "statistical analysis",
    "bayesian hierarchical modeling",
    "linear regression",
    "logistic regression",
    "machine learning algorithms",
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
    "natural language processing",
    "data mining",
    "data modeling",
    "predictive modeling",
    "statistical analysis",
    "bayesian hierarchical modeling",
    "linear regression",
    "logistic regression",
    "machine learning algorithms",
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
    "aws",
    "azure",
    "azure machine learning",
    "bash",
    "c++",
    "cassandra",
    "couchbase",
    "docker",
    "dynamodb",
    "ec2",
    "hadoop",
    "hive",
    "impala",
    "java",
    "jenkins",
    "jira",
    "kafka",
    "kubernetes",
    "linux",
    "matlab",
    "mongodb",
    "mysql",
    "oracle cloud",
    "redshift",
    "scala",
    "splunk enterprise",
    "spss",
    "sql server",
    "terraform",
    "alteryx",
    "ansible",
]

TAILORING_FACET_PATTERNS = {
    "tooling_languages": [
        "python",
        "sql",
        "r",
        "sas",
        "tableau",
        "looker",
        "power bi",
        "databricks",
        "spark",
    ],
    "statistics_modeling": [
        "statistics",
        "statistical",
        "statistical methods",
        "statistical analysis",
        "statistical modeling",
        "modeling",
        "forecasting",
        "prediction",
        "regression",
        "classification",
        "predictive modeling",
        "linear regression",
        "logistic regression",
        "bayesian hierarchical modeling",
    ],
    "experimentation": [
        "a/b test",
        "a/b testing",
        "experiment",
        "experimentation",
        "experimental design",
        "hypothesis testing",
        "incrementality",
        "quasi-experimental",
        "diff-in-diff",
        "propensity",
        "synthetic control",
    ],
    "causal_inference": [
        "causal inference",
        "bayesian",
    ],
    "data_engineering": [
        "data engineering",
        "data pipeline",
        "pipelines",
        "etl",
        "elt",
        "spark",
        "airflow",
        "dbt",
        "snowflake",
        "bigquery",
        "redshift",
        "databricks",
        "kafka",
        "hadoop",
    ],
    "bi_reporting": [
        "tableau",
        "looker",
        "power bi",
        "dashboard",
        "dashboards",
        "reporting",
        "visualization",
    ],
    "ml_methods": [
        "machine learning",
        "machine learning algorithms",
        "deep learning",
        "natural language processing",
        "classification",
        "regression",
        "forecasting",
        "predictive modeling",
    ],
    "domain_context": DOMAIN_SIGNAL_PATTERNS + [
        "streaming",
        "advertising",
        "marketplace",
        "media",
    ],
}

BASELINE_FAMILIARITY_FAMILIES = {
    "notebook_workflow": {
        "job_terms": [
            "jupyter",
            "jupyter notebook",
            "jupyter notebooks",
        ],
        "title_tokens_any": [
            "scientist",
            "analyst",
            "research",
            "machine",
            "learning",
            "ai",
        ],
        "supporting_explicit_skills_any": [
            "python",
            "pandas",
            "numpy",
            "scikit-learn",
            "tensorflow",
            "pytorch",
            "spark",
            "databricks",
        ],
        "supporting_analytics_signals_any": [
            "machine learning",
            "modeling",
            "analysis",
            "statistics",
            "data science",
        ],
        "supporting_tooling_signals_any": [
            "python",
            "spark",
            "databricks",
            "tensorflow",
            "pytorch",
        ],
        "min_support_hits": 2,
    },
    "version_control": {
        "job_terms": [
            "git",
            "github",
            "gitlab",
            "bitbucket",
            "version control",
            "source control",
            "source code management",
        ],
        "title_tokens_any": [
            "engineer",
            "scientist",
            "analyst",
            "research",
            "machine",
            "learning",
            "ai",
        ],
        "supporting_explicit_skills_any": [
            "python",
            "sql",
            "r",
            "dbt",
            "airflow",
            "spark",
            "pytorch",
            "tensorflow",
        ],
        "supporting_analytics_signals_any": [
            "machine learning",
            "modeling",
            "analysis",
            "data science",
        ],
        "supporting_tooling_signals_any": [
            "python",
            "sql",
            "dbt",
            "airflow",
            "spark",
            "pytorch",
            "tensorflow",
        ],
        "min_support_hits": 1,
    },
    "classical_ml_methods": {
        "job_terms": [
            "random forest",
            "random forests",
            "svm",
            "support vector machine",
            "support vector machines",
            "linear regression",
            "logistic regression",
        ],
        "title_tokens_any": [
            "scientist",
            "analyst",
            "research",
            "machine",
            "learning",
            "ai",
        ],
        "supporting_explicit_skills_any": [
            "python",
            "scikit-learn",
            "machine learning",
            "regression",
            "classification",
            "statistical modeling",
        ],
        "supporting_analytics_signals_any": [
            "machine learning",
            "modeling",
            "classification",
            "regression",
            "statistics",
            "statistical",
        ],
        "supporting_tooling_signals_any": [
            "python",
            "scikit-learn",
        ],
        "min_support_hits": 2,
    },
    "model_development_basics": {
    "job_terms": [
        "predictive modeling",
        "data modeling",
        "machine learning algorithms",
    ],
    "title_tokens_any": [
        "scientist",
        "analyst",
        "research",
        "machine",
        "learning",
        "ai",
    ],
    "supporting_explicit_skills_any": [
        "python",
        "scikit-learn",
        "machine learning",
        "regression",
        "classification",
        "statistical modeling",
    ],
    "supporting_analytics_signals_any": [
        "machine learning",
        "modeling",
        "classification",
        "regression",
        "statistics",
        "statistical",
        "data science",
    ],
    "supporting_tooling_signals_any": [
        "python",
        "scikit-learn",
        "tensorflow",
        "pytorch",
    ],
    "min_support_hits": 2,
},
}

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
    "a/b experiment": "a/b testing",
    "a/b experiments": "a/b testing",
    "experiment": "experimentation",
    "experiments": "experimentation",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "powerbi": "power bi",
    "dashboard": "dashboard",
    "dashboards": "dashboard",
    "pipeline": "pipeline",
    "pipelines": "pipeline",
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

GENERIC_REQUIRED_SKILL_TARGETS = {
    *_ANALYTICS_ML_GENERIC_SIGNALS,
    "analysis",
    "experiment",
    "experimentation",
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
    r"\bwe['’]d love to chat if you have\b",
    r"\bwe would love to chat if you have\b",
    r"\bskills\s*&\s*attributes\b",
    r"\bskills and attributes\b",
    r"\bwhat you bring\b",
    r"\bwhat you'll bring\b",
    r"\bwhat you will bring\b",
    r"\byou should bring\b",
]

RESPONSIBILITY_CONTEXT_PATTERNS = [
    r"\bresponsibilities\b",
    r"\bcore responsibilities\b",
    r"\bwhat you['’]ll do\b",
    r"\bwhat you will do\b",
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

# ============================================================
# TAILORING CONSTANTS
# ============================================================

ACTION_VERB_HINTS = [
    "achieved",
    "analyzed",
    "architected",
    "automated",
    "built",
    "conducted",
    "created",
    "deduced",
    "delivered",
    "designed",
    "developed",
    "drove",
    "enhanced",
    "evaluated",
    "generated",
    "identified",
    "implemented",
    "improved",
    "increased",
    "led",
    "leveraged",
    "managed",
    "manipulated",
    "modeled",
    "optimized",
    "performed",
    "predicted",
    "reduced",
    "streamlined",
    "supported",
    "used",
]

TAILORING_ROLE_FAMILY_FALLBACK = "general_data_science"

TAILORING_ROLE_FRAMING_PROFILES = {
    "marketing_experimentation_ds": {
        "title_tokens_any": [
            "marketing",
            "growth",
            "product",
            "lifecycle",
            "customer",
            "campaign",
            "decision",
        ],
        "signal_terms_any": [
            "campaign",
            "campaigns",
            "conversion",
            "conversions",
            "targeting",
            "targeted",
            "segmentation",
            "personalization",
            "personalized",
            "customized",
            "incrementality",
            "lift",
            "uplift",
            *EXPERIMENTATION_SIGNAL_PATTERNS,
            *TAILORING_FACET_PATTERNS["experimentation"],
            *TAILORING_FACET_PATTERNS["causal_inference"],
        ],
        "facet_priority_order": [
            "experimentation",
            "causal_inference",
            "statistics_modeling",
            "ml_methods",
            "bi_reporting",
            "domain_context",
        ],
        "ats_priority_terms_any": [
            "a/b testing",
            "experimentation",
            "causal inference",
            "incrementality",
            "conversion",
            "segmentation",
            "targeting",
            "campaign",
        ],
        "appeal_targets": [
            "show optimization or experimentation ownership clearly",
            "surface business lever language like campaign, targeting, segmentation, or conversion",
            "make decision or measurement consequence explicit",
            "prefer quantified lift or rate movement when present in the evidence",
        ],
    },
    "risk_pricing_ds": {
        "title_tokens_any": [
            "risk",
            "credit",
            "fraud",
            "pricing",
            "underwriting",
            "portfolio",
            "insurance",
        ],
        "signal_terms_any": [
            "risk",
            "credit",
            "fraud",
            "pricing",
            "underwriting",
            "portfolio",
            "insurance",
            "lapse",
            "loss",
            "exposure",
            "default",
            "profitability",
            "forecasting",
            *TAILORING_FACET_PATTERNS["statistics_modeling"],
            *TAILORING_FACET_PATTERNS["ml_methods"],
            *DOMAIN_SIGNAL_PATTERNS,
        ],
        "facet_priority_order": [
            "statistics_modeling",
            "ml_methods",
            "data_engineering",
            "domain_context",
            "bi_reporting",
        ],
        "ats_priority_terms_any": [
            "risk",
            "credit",
            "pricing",
            "portfolio",
            "forecasting",
            "regression",
            "classification",
            "insurance",
        ],
        "appeal_targets": [
            "show decision support tied to pricing, underwriting, risk, or portfolio outcomes",
            "make business consequence explicit, such as loss reduction, lapse reduction, exposure analysis, or profitability impact",
            "prefer language that shows ownership of analytical decision support rather than passive reporting",
        ],
    },
    "analytics_bi": {
        "title_tokens_any": [
            "analyst",
            "analytics",
            "business",
            "reporting",
            "insights",
            "operations",
        ],
        "signal_terms_any": [
            "dashboard",
            "dashboards",
            "reporting",
            "visualization",
            "insights",
            "analysis",
            "analytics",
            *TAILORING_FACET_PATTERNS["bi_reporting"],
            *TAILORING_FACET_PATTERNS["tooling_languages"],
        ],
        "facet_priority_order": [
            "bi_reporting",
            "tooling_languages",
            "statistics_modeling",
            "domain_context",
        ],
        "ats_priority_terms_any": [
            "sql",
            "tableau",
            "looker",
            "power bi",
            "dashboard",
            "reporting",
            "analytics",
        ],
        "appeal_targets": [
            "show how analysis informed a decision, workflow, or operational action",
            "prefer business-facing insight framing over tool listing",
            "make stakeholder or process impact explicit when supported by evidence",
        ],
    },
    "machine_learning_engineering": {
        "title_tokens_any": [
            "machine",
            "learning",
            "ml",
            "ai",
            "applied",
            "research",
            "engineer",
        ],
        "signal_terms_any": [
            "machine learning",
            "deep learning",
            "natural language processing",
            "modeling",
            "prediction",
            "classification",
            "regression",
            "deployment",
            "production",
            "latency",
            "scalability",
            *TAILORING_FACET_PATTERNS["ml_methods"],
            *TAILORING_FACET_PATTERNS["data_engineering"],
            *TOOLING_SIGNAL_PATTERNS,
        ],
        "facet_priority_order": [
            "ml_methods",
            "data_engineering",
            "tooling_languages",
            "statistics_modeling",
            "domain_context",
        ],
        "ats_priority_terms_any": [
            "machine learning",
            "python",
            "spark",
            "tensorflow",
            "pytorch",
            "classification",
            "regression",
            "forecasting",
        ],
        "appeal_targets": [
            "show model-development ownership, not just model mention",
            "make production or scale context explicit when supported",
            "prefer end-to-end method plus outcome framing over tool pileups",
        ],
    },
    "general_data_science": {
        "title_tokens_any": [
            "data",
            "scientist",
            "applied",
            "research",
            "analytics",
            "decision",
        ],
        "signal_terms_any": [
            *ANALYTICS_ML_SIGNAL_PATTERNS,
            *EXPERIMENTATION_SIGNAL_PATTERNS,
            *DOMAIN_SIGNAL_PATTERNS,
        ],
        "facet_priority_order": [
            "statistics_modeling",
            "ml_methods",
            "experimentation",
            "tooling_languages",
            "domain_context",
            "bi_reporting",
        ],
        "ats_priority_terms_any": [
            "machine learning",
            "statistics",
            "modeling",
            "forecasting",
            "regression",
            "classification",
            "analytics",
            "experimentation",
        ],
        "appeal_targets": [
            "make action, method, business context, and outcome read in that order when possible",
            "prefer explicit impact framing over generic technical description",
            "surface the strongest supported JD-aligned term without keyword stuffing",
        ],
    },
}

TAILORING_WRITER_STRONG_GAIN_TARGETS = [
    "stronger_supported_jd_signal_salience",
    "stronger_supported_business_result_framing",
    "stronger_specificity",
]

TAILORING_STYLE_ONLY_CHURN_HINTS = [
    "leveraging",
    "utilizing",
    "to enhance",
    "to improve",
    "which enhanced",
    "which improved",
]

# ============================================================
# REPLACEMENT SELECTION
# ============================================================

_BAD_COUNTERFACTUAL_STATUSES = {
    "bullet_id_not_found",
    "bullet_id_not_unique",
    "bullet_index_out_of_range",
    "raw_text_bullet_not_found",
    "raw_text_bullet_not_unique",
    "missing_patch_inputs",
    "unsupported_operation",
}

_DIRECT_APPLY_READY_MATERIALITY_STATUSES = {
    "material_candidate",
}

_DIRECT_APPLY_OPTIONAL_MATERIALITY_STATUSES = {
    "export_safe_no_score_lift",
}


# ============================================================
# SCORING V2
# ============================================================

RESUME_METHOD_SIGNAL_PATTERNS = list(dict.fromkeys(
    ANALYTICS_ML_SIGNAL_PATTERNS + EXPERIMENTATION_SIGNAL_PATTERNS
))

RESUME_WORKFLOW_SIGNAL_PATTERNS = list(dict.fromkeys([
    "a/b test",
    "a/b testing",
    "experiment",
    "experimentation",
    "automation",
    "forecasting",
    "segmentation",
    "cohort analysis",
    "customer lifecycle analysis",
    "lifecycle analysis",
    "revenue analysis",
    "reporting",
    "reporting framework",
    "reporting frameworks",
    "dashboard",
    "dashboards",
    "visualization",
    "data quality",
    "etl",
    "elt",
    "pipeline",
    "pipelines",
    "lead flow",
    "handoff",
    "eda",
]))

RESUME_BUSINESS_CONTEXT_SIGNAL_PATTERNS = list(dict.fromkeys(
    TAILORING_FACET_PATTERNS["domain_context"]
    + [
        "growth",
        "product-led growth",
        "plg",
        "revenue",
        "retention",
        "expansion",
        "contraction",
        "sales intelligence",
        "customer success",
        "marketing",
        "finance",
        "public safety",
        "customer lifecycle",
    ]
))

RESUME_STAKEHOLDER_CONTEXT_SIGNAL_PATTERNS = list(dict.fromkeys([
    "stakeholder",
    "stakeholders",
    "executive",
    "executives",
    "non-technical",
    "customers",
    "agencies",
    "product",
    "marketing",
    "finance",
    "sales",
    "customer success",
    "engineering",
    "leadership",
    "leaders",
]))

RESUME_ARTIFACT_TYPE_SIGNAL_PATTERNS = list(dict.fromkeys([
    "dashboard",
    "dashboards",
    "visualization",
    "visualizations",
    "report",
    "reports",
    "analysis",
    "analyses",
    "model",
    "models",
    "summary",
    "summaries",
    "presentation",
    "presentations",
    "framework",
    "frameworks",
    "query",
    "queries",
    "script",
    "scripts",
]))

RESUME_KPI_METRIC_SIGNAL_PATTERNS = list(dict.fromkeys([
    "kpi",
    "kpis",
    "conversion",
    "retention",
    "revenue",
    "margin",
    "profitability",
    "pipeline",
    "roi",
    "attribution",
    "engagement",
    "adoption",
    "quality",
    "efficiency",
    "churn",
]))

RESUME_OWNERSHIP_SIGNAL_PATTERNS = list(dict.fromkeys(
    ACTION_VERB_HINTS
    + [
        "owned",
        "partnered",
        "collaborated",
        "presented",
        "translated",
        "advised",
        "mentored",
    ]
))

_WORKFLOW_CANDIDATES = [
    "a/b testing",
    "experimentation",
    "automation",
    "reporting",
    "reporting frameworks",
    "dashboard",
    "dashboards",
    "visualization",
    "forecasting",
    "attribution",
    "customer lifecycle analysis",
    "lifecycle analysis",
    "cohort analysis",
    "data quality",
    "etl",
    "elt",
    "pipeline",
    "pipelines",
    "revenue analysis",
    "lead flow",
    "handoff",
    "segmentation",
    "eda",
]

_BUSINESS_CONTEXT_CANDIDATES = [
    "growth",
    "product-led growth",
    "plg",
    "revenue",
    "retention",
    "expansion",
    "contraction",
    "sales intelligence",
    "customer success",
    "marketing",
    "finance",
    "public safety",
    "healthcare",
    "fraud",
    "risk",
    "operations",
    "supply chain",
    "customer lifecycle",
]

_STAKEHOLDER_CONTEXT_CANDIDATES = [
    "stakeholders",
    "executive",
    "non-technical",
    "product",
    "marketing",
    "finance",
    "sales",
    "customer success",
    "engineering",
    "customers",
    "agencies",
    "leaders",
]

_KPI_METRIC_CANDIDATES = [
    "kpi",
    "kpis",
    "conversion",
    "retention",
    "revenue",
    "margin",
    "profitability",
    "roi",
    "attribution",
    "engagement",
    "adoption",
    "quality",
    "efficiency",
    "churn",
]

_OWNERSHIP_SIGNAL_CANDIDATES = [
    "own",
    "ownership",
    "lead",
    "leader",
    "trusted advisor",
    "thought leader",
    "drive",
    "mentor",
    "highly visible",
    "independent",
    "autonomy",
]

_VARIANT_TITLE_ABBREVIATIONS = {
    "ai": "ai engineer",
    "mle": "machine learning engineer",
    "ml": "machine learning engineer",
    "ds": "data scientist",
    "da": "data analyst",
    "ae": "analytics engineer",
}


_REWRITE_OUTCOME_DISPLAY_LABELS = {
    "material_candidate": "Best now",
    "export_safe_no_score_lift": "Safe but optional",
    "directional_only": "Direction only",
    "cosmetic_only": "Cosmetic only",
    "patch_ready": "Ready",
}

_REWRITE_CLAIM_SAFETY_DISPLAY_LABELS = {
    "safe_strengthen": "Directly supported",
    "keep_visible": "Keep visible",
    "adjacent_only": "Adjacent support only",
    "safe_reorder": "Reorder only",
    "safe_merge": "Merge guidance",
    "safe_suppress": "Suppress guidance",
}

_REWRITE_GROUP_DISPLAY_LABELS = {
    "high_confidence_rewrites": "Best now",
    "export_safe_rewrites": "Safe but optional",
    "directional_only": "Direction only",
}

_PROMOTABLE_SIGNAL_FAMILY_LABELS = {
    "experimentation": "Experimentation",
    "analytics_ml": "Modeling",
}

_PROMOTABLE_SIGNAL_FAMILY_REQUIRED_DIMENSIONS = {
    "experimentation": {"experimentation_depth"},
    "analytics_ml": {"analytics_ml_depth"},
}

_CLAUSE_SPLIT_ACTION_VERBS = (
    "Implemented",
    "Designed",
    "Developed",
    "Built",
    "Created",
    "Led",
    "Ran",
    "Conducted",
    "Engineered",
    "Automated",
    "Performed",
)

_STRUCTURAL_CLAUSE_FAMILY_PRIORITY = {
    "experimentation": 0,
    "analytics_ml": 1,
}

_REWRITE_REVIEW_STATE_DISPLAY_LABELS = {
    "pending": "Pending",
    "accepted": "Accepted",
    "rejected": "Rejected",
    "edited_after_accept": "Edited after accept",
}

_ALLOWED_REWRITE_REVIEW_STATES = {
    "pending",
    "accepted",
    "rejected",
    "edited_after_accept",
}