import re
import pycountry

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

#Ashby queries
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

# compiled regex (done once at import)
TITLE_INCLUDE_REGEX = [re.compile(p, re.I) for p in TITLE_INCLUDE_PATTERNS]
TITLE_EXCLUDE_REGEX = [re.compile(p, re.I) for p in TITLE_EXCLUDE_PATTERNS]

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS",
    "KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY",
    "NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV",
    "WI","WY"
}

US_STATE_NAMES = {
"ALABAMA","ALASKA","ARIZONA","ARKANSAS","CALIFORNIA","COLORADO","CONNECTICUT",
"DELAWARE","FLORIDA","GEORGIA","HAWAII","IDAHO","ILLINOIS","INDIANA","IOWA",
"KANSAS","KENTUCKY","LOUISIANA","MAINE","MARYLAND","MASSACHUSETTS","MICHIGAN",
"MINNESOTA","MISSISSIPPI","MISSOURI","MONTANA","NEBRASKA","NEVADA",
"NEW HAMPSHIRE","NEW JERSEY","NEW MEXICO","NEW YORK","NORTH CAROLINA",
"NORTH DAKOTA","OHIO","OKLAHOMA","OREGON","PENNSYLVANIA","RHODE ISLAND",
"SOUTH CAROLINA","SOUTH DAKOTA","TENNESSEE","TEXAS","UTAH","VERMONT",
"VIRGINIA","WASHINGTON","WEST VIRGINIA","WISCONSIN","WYOMING"
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

# compiled regex used for location parsing
TOKEN_SPLIT_REGEX = re.compile(r"[,\-\s]+")

# regex used in title normalization
PUNCT_REGEX = re.compile(r"[^\w\s]")
ROMAN_SUFFIX_REGEX = re.compile(r"\s+(i|ii|iii|iv|v)$")
WHITESPACE_REGEX = re.compile(r"\s+")

# build country set once
ALL_COUNTRIES = {c.name.upper() for c in pycountry.countries}
ALL_COUNTRIES.update({
    "UK",
    "U.K.",
    "UNITED KINGDOM",
    "KOREA",
    "SOUTH KOREA",
    "NORTH KOREA",
})

# ATS identifiers (prevents string typos)
SUPPORTED_ATS = ["greenhouse", "lever", "workday", "ashby", "workable", "jobvite"]

ATS_WORKDAY = "workday"
ATS_LEVER = "lever"
ATS_JOBVITE = "jobvite"
ATS_GREENHOUSE = "greenhouse"
ATS_ASHBY = "ashby"
ATS_WORKABLE = "workable"

# ATS URLs and GraphQL queries
GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{}/jobs"
ASHBY_URL = "https://jobs.ashbyhq.com/api/non-user-graphql"
JOBVITE_URL_PATTERNS = [
    "https://jobs.jobvite.com/{company}/jobs/alljobs",
    "https://jobs.jobvite.com/{company}/jobs",
]
LEVER_API = "https://api.lever.co/v0/postings"
WORKABLE_V3_API = "https://apply.workable.com/api/v3/accounts/{}/jobs"
WORKABLE_V1_API = "https://apply.workable.com/api/v1/widget/accounts/{}"
WORKABLE_V2_DETAIL_API = "https://apply.workable.com/api/v2/accounts/{}/jobs/{}"
WORKDAY_API_URL_TEMPLATE = "https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
WORKDAY_ORIGIN_TEMPLATE = "https://{host}.myworkdayjobs.com"

# Timestamp settings and workers for concurrent fetching
TIMESTAMP_WORKERS = 10
DATE_ONLY_HOUR = 12
FRESHNESS_HOURS = 24

#ATS Detection and discovery
SLUG_REGEX = re.compile(r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)")

INVALID_SLUGS = {
    "careers",
    "jobs",
    "job",
    "apply",
    "board",
    "boards",
    "hiring",
    "-----",
    "------"
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
    "team"
]

WORKDAY_REGEX = re.compile(
    r"https://[a-zA-Z0-9-]+\.wd[0-9]+\.myworkdayjobs\.com/[a-zA-Z0-9_-]+"
)

INVALID_GREENHOUSE_SLUGS = {
    "job",
    "jobs",
    "apply",
    "careers",
    "boards",
    "greenhouse",
}

#Greenhouse discovery

GREENHOUSE_PATTERNS = [
    r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)",
    r"job-boards\.greenhouse\.io/([a-zA-Z0-9_-]+)",
]

#ALL ATS DISCOVERY

ATS_REGEX = {
    "greenhouse": [
        re.compile(r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)", re.I),
        re.compile(r"boards\.greenhouse\.io/embed/job_board.*?for=([a-zA-Z0-9_-]+)", re.I),
    ],

    "lever": [
        re.compile(r"jobs\.lever\.co/([a-zA-Z0-9_-]+)", re.I)
    ],

    "ashby": [
        re.compile(r"jobs\.ashbyhq\.com/([a-zA-Z0-9_-]+)", re.I)
    ],

    "workable": [
        re.compile(r"apply\.workable\.com/([a-zA-Z0-9_-]+)", re.I)
    ],

    "jobvite": [
        re.compile(r"jobs\.jobvite\.com/([a-zA-Z0-9_-]+)", re.I)
    ],

    "workday": [
        re.compile(r"myworkdayjobs\.com/([^/]+)/", re.I)
    ],

    "smartrecruiters": [
    re.compile(r"jobs\.smartrecruiters\.com/([a-zA-Z0-9\-_]+)", re.I)
    ],
}

#SITEMAP
SITEMAP_PATHS = [
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/sitemap1.xml",
    "/sitemap-careers.xml",
    "/sitemap_jobs.xml"
]

#Misc.

COMPANY_SUFFIXES = [
    "inc", "inc.", "llc", "l.l.c", "corp", "corporation",
    "co", "company", "ltd", "limited", "plc"
]

#SEARCH ENGINE DISCOVERY
SEARCH_URL = "https://lite.duckduckgo.com/lite/?q={}&s={}"

ATS_PATTERNS = {
    "lever": re.compile(r"jobs\.lever\.co/([a-zA-Z0-9\-]+)"),
    "ashby": re.compile(r"jobs\.ashbyhq\.com/([a-zA-Z0-9\-]+)"),
    "workable": re.compile(r"apply\.workable\.com/([a-zA-Z0-9\-]+)"),
    "jobvite": re.compile(r"jobs\.jobvite\.com/([a-zA-Z0-9\-]+)")
}

ATS_SITES = {
    "lever": "site:jobs.lever.co",
    "ashby": "site:jobs.ashbyhq.com",
    "workable": "site:apply.workable.com",
    "jobvite": "site:jobs.jobvite.com"
}

SEARCH_JOB_TITLES = [
    "software engineer",
    "data scientist",
    "machine learning engineer",
    # "ai engineer",
    # "data analyst",
    # "research scientist",
    # "applied scientist",
]

#GITHUB SEARCH DISCOVERY

GITHUB_SEARCH = "https://api.github.com/search/code?q={}&per_page=100"

ATS_PATTERNS = {
    "greenhouse": re.compile(r"boards\.greenhouse\.io/([a-zA-Z0-9\-]+)"),
    "lever": re.compile(r"jobs\.lever\.co/([a-zA-Z0-9\-]+)"),
    "ashby": re.compile(r"jobs\.ashbyhq\.com/([a-zA-Z0-9\-]+)"),
    "workable": re.compile(r"apply\.workable\.com/([a-zA-Z0-9\-]+)"),
}

QUERIES = [
    "boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "apply.workable.com"
]


# AI AGENTS EVAL

BASE_SKILL_PATTERNS = [
    "python",
    "pytorch",
    "tensorflow",
    "sql",
    "spark",
    "scikit",
    "pandas",
    "numpy"
]

BASE_AI_FLAG_PATTERNS = {
    "genai": ["generative ai", "genai"],
    "llm": ["large language model", "llm"],
    "rag": ["retrieval augmented", "rag"],
    "ml_platform": ["ml platform", "mlops"],
    "research": ["research scientist", "research"]
}

BASE_SENIORITY_PATTERNS = {
    "senior": ["senior", "staff", "principal"],
    "mid": ["engineer", "scientist"],
    "junior": ["junior", "associate"]
}

#visa sponsorship detection
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
    r"authorized to work in the (united states|us|u\.s\.)"
]

POSITIVE_VISA_PATTERNS = [
    r"h-?1b",
    r"visa sponsorship",
    r"sponsor",
    r"work authorization.*provided",
    r"opt",
    r"cpt"
]

#SKILLS extraction

SECTION_PATTERNS = {
    "required": [
        r"minimum qualifications",
        r"basic qualifications",
        r"required qualifications",
        r"requirements",
        r"what you'll need",
        r"must have"
    ],
    "preferred": [
        r"preferred qualifications",
        r"nice to have",
        r"bonus qualifications",
        r"good to have",
        r"plus"
    ]
}

SKILL_STOPWORDS = {
    "model",
    "models",
    "modeling",
    "maintain",
    "maintaining",
    "detail",
    "details",
    "paid",
    "available",
    "language",
    "languages",
    "seamless",
    "blair"
}

DOMAIN_STOPWORDS = {
    "obtain",
    "entertainment",
    "domain",
    "domains",
    "industry",
    "business",
    "operations",
    "scientist",
    "engineering",
    "research",
    "strategy",
    "constraints",
    "imbalances",
    "metrics",
    "organization",
    "company"
}
TRUSTED_CORE_SKILLS = {
    "python",
    "sql",
    "pandas",
    "spark",
    "pytorch",
    "tensorflow",
    "airflow",
    "aws",
    "gcp",
    "azure",
    "databricks",
    "snowflake",
    "tableau",
    "powerbi",
    "scikit-learn",
    "xgboost",
    "langchain"
}

# Words that should never appear as skills
INVALID_SKILL_WORDS = {
    "build",
    "create",
    "obtain",
    "maintain",
    "raise",
    "improve",
    "support",
    "entertainment",
    "industry",
    "business",
    "domain",
    "team",
    "stakeholder",
    "ability",
    "experience",
    "understanding",
    "knowledge",
    "training",
    "emailing",
    "deployment",
    "validation",
    "development",
    "processing",
    "pipeline",
    "monitoring",
}

# Technology taxonomy examples (used only to guide LLM reasoning)

TECH_CATEGORY_EXAMPLES = {

    "programming_languages": [
        "python",
        "r",
        "scala",
        "java",
        "c++",
        "go",
        "rust"
    ],

    "data_libraries": [
        "pandas",
        "numpy",
        "scipy",
        "scikit-learn",
        "xgboost",
        "lightgbm"
    ],

    "deep_learning": [
        "pytorch",
        "tensorflow",
        "keras"
    ],

    "llm_ai": [
        "transformers",
        "huggingface",
        "langchain",
        "rag",
        "embeddings",
        "vector databases"
    ],

    "data_engineering": [
        "spark",
        "flink",
        "kafka",
        "dbt",
        "airflow",
        "dagster",
        "prefect"
    ],

    "databases": [
        "postgres",
        "mysql",
        "snowflake",
        "bigquery",
        "redshift",
        "duckdb"
    ],

    "cloud_platforms": [
        "aws",
        "gcp",
        "azure"
    ],

    "infrastructure": [
        "docker",
        "kubernetes",
        "terraform",
        "ray"
    ],

    "visualization": [
        "tableau",
        "powerbi",
        "looker"
    ],

    "version_control": [
        "git",
        "github",
        "gitlab"
    ],

    # NEW
    "data_science_methods": [
        "a/b testing",
        "causal inference",
        "bayesian inference",
        "hypothesis testing",
        "experimental design",
        "statistical modeling",
        "time series forecasting",
        "time series analysis",
        "feature engineering",
        "model evaluation",
        "cross validation"
    ]
}

NORMALIZATION_MAP = {
    "llm apis": "llm",
    "large language models": "llm",
    "retrievalbased ai systems": "rag",
    "vector databases": "vector db",
    "scikitlearn": "scikit-learn",
    "scikit": "scikit-learn",
    "sklearn": "scikit-learn",
}

TECH_KEYWORDS = [
    "python",
    "spark",
    "pytorch",
    "tensorflow",
    "langchain",
    "transformer",
    "huggingface",
    "vector",
    "embedding",
    "rag",
    "llm",
    "scikit",
    "xgboost",
]

COMMON_WORDS = {
"coverage","leverage","platform","enable","support",
"analysis","pipeline","system","service","solution"
}

GENERIC_SKILL_PHRASES = {
    "model training",
    "model validation",
    "data preprocessing",
    "pipeline development",
    "distributed systems",
    "cloud computing",
    "ml frameworks",
}