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
    r"principal"
]

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

CAREER_PATHS = [
    "",
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
    "opportunities"
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

#RANKING

#Misc.

COMPANY_SUFFIXES = [
    "inc", "inc.", "llc", "l.l.c", "corp", "corporation",
    "co", "company", "ltd", "limited", "plc"
]