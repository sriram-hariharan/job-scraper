from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import requests
import pycountry

from models.job import Job
from src.config.consts import (
    HIMALAYAS_MAX_DESCRIPTION_CHARS,
    HIMALAYAS_MAX_PAGES_PER_PROFILE,
    HIMALAYAS_MAX_QUERY_PROFILES,
    HIMALAYAS_MAX_RESPONSE_BYTES,
    HIMALAYAS_QUERY_PROFILES_PATH,
    HIMALAYAS_RESULTS_PER_PAGE,
    HIMALAYAS_SEARCH_API,
    SCRAPER_HTTP_TIMEOUT_SECONDS,
    SCRAPER_RETRY_ATTEMPTS,
)
from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.utils.http_retry import retry_request
from src.utils.logging import get_logger
from src.utils.pipeline_metrics import observe_acquisition


logger = get_logger("himalayas")

_PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_COMPANY_SLUG_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
_TIMEZONE_PATTERN = re.compile(
    r"^(?:UTC)?[+-](?:0?\d|1[0-4])(?::(?:00|30|45))?$",
    re.IGNORECASE,
)
_GUID_PATTERN = re.compile(r"^[^\s\x00-\x1f\x7f]{1,200}$")
_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
_JOB_PATH_PATTERN = re.compile(
    r"^/companies/[a-z0-9][a-z0-9-]*/jobs/[a-z0-9][a-z0-9-]*/?$",
    re.IGNORECASE,
)
_JSON_MEDIA_TYPES = frozenset({"application/json", "text/json"})
_RETRY_STATUSES = frozenset({500, 502, 503, 504})
_ALLOWED_PROFILE_KEYS = frozenset(
    {
        "profile_id",
        "query",
        "country",
        "worldwide",
        "exclude_worldwide",
        "seniority",
        "employment_type",
        "company_slugs",
        "timezone",
        "sort",
    }
)
_SENIORITY_VALUES = frozenset(
    {"Entry-level", "Mid-level", "Senior", "Manager", "Director", "Executive"}
)
_EMPLOYMENT_TYPE_VALUES = frozenset(
    {"Full Time", "Part Time", "Contractor", "Temporary", "Intern", "Volunteer", "Other"}
)
_SORT_VALUES = frozenset(
    {"relevant", "recent", "salaryAsc", "salaryDesc", "nameAToZ", "nameZToA", "jobs"}
)
_SALARY_PERIOD_VALUES = frozenset(
    {"hourly", "weekly", "fortnightly", "monthly", "annual"}
)
_BLOCK_TAGS = frozenset(
    {
        "article",
        "blockquote",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
)
_SUPPRESSED_TAGS = frozenset(
    {"button", "form", "iframe", "script", "select", "style", "textarea"}
)
_VISIBLE_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_APPLICATION_FLOW_PATTERN = re.compile(
    r"\b(?:how to apply|apply (?:at|now|online|through|via)|"
    r"submit(?: your| a)? (?:application|resume)|upload(?: your| a)? resume|"
    r"application form|candidate portal|resume upload)\b",
    re.IGNORECASE,
)
_PROHIBITED_URL_PATH_PARTS = (
    "/account",
    "/apply",
    "/application",
    "/candidate",
    "/employer",
    "/login",
    "/redirect",
    "/resume",
    "/sign-in",
    "/signup",
    "/tracking",
)
_MAX_PROFILE_LIST_ITEMS = 20
_MAX_METADATA_LIST_ITEMS = 100
_EARLIEST_PLAUSIBLE_TIMESTAMP = datetime(2000, 1, 1, tzinfo=timezone.utc)
_MAX_TIMESTAMP_FUTURE_DAYS = 3_660


class _InvalidConfiguration(ValueError):
    pass


class _MalformedPayload(ValueError):
    pass


class _PlainTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._parts = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag, attrs):
        safe_tag = str(tag or "").lower()
        if self._suppressed_depth:
            self._suppressed_depth += 1
        elif safe_tag == "input":
            return
        elif safe_tag in _SUPPRESSED_TAGS:
            self._suppressed_depth = 1
        elif safe_tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if not self._suppressed_depth and str(tag or "").lower() in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if self._suppressed_depth:
            self._suppressed_depth -= 1
        elif str(tag or "").lower() in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if not self._suppressed_depth and data:
            self._parts.append(data)

    def text(self):
        return "".join(self._parts)


def _clean_text(value, *, maximum=10_000):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:maximum].rstrip()


def _profile_text(value, *, maximum):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise _InvalidConfiguration("invalid profile string")
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) > maximum:
        raise _InvalidConfiguration("profile string exceeds bound")
    return text


def _normalize_enum_list(value, *, allowed):
    if value is None:
        return ()
    if not isinstance(value, list) or len(value) > _MAX_PROFILE_LIST_ITEMS:
        raise _InvalidConfiguration("invalid profile enum collection")
    normalized = []
    for item in value:
        if not isinstance(item, str):
            raise _InvalidConfiguration("invalid profile enum")
        clean = item.strip()
        if clean not in allowed:
            raise _InvalidConfiguration("invalid profile enum")
        if clean not in normalized:
            normalized.append(clean)
    return tuple(normalized)


def _normalize_company_slugs(value):
    if value is None:
        return ()
    if not isinstance(value, list) or len(value) > _MAX_PROFILE_LIST_ITEMS:
        raise _InvalidConfiguration("invalid company slug collection")
    normalized = []
    for item in value:
        if not isinstance(item, str):
            raise _InvalidConfiguration("invalid company slug")
        slug = item.strip()
        if slug != slug.lower() or not _COMPANY_SLUG_PATTERN.fullmatch(slug):
            raise _InvalidConfiguration("invalid company slug")
        if slug not in normalized:
            normalized.append(slug)
    return tuple(normalized)


def _normalize_profile(value):
    if not isinstance(value, dict) or set(value) - _ALLOWED_PROFILE_KEYS:
        raise _InvalidConfiguration("invalid profile object")

    raw_profile_id = value.get("profile_id")
    if not isinstance(raw_profile_id, str):
        raise _InvalidConfiguration("invalid profile id")
    profile_id = raw_profile_id.strip()
    if not _PROFILE_ID_PATTERN.fullmatch(profile_id):
        raise _InvalidConfiguration("invalid profile id")

    query = _profile_text(value.get("query"), maximum=200)
    country = _profile_text(value.get("country"), maximum=100)
    timezone_value = _profile_text(value.get("timezone"), maximum=16)
    if timezone_value and not _TIMEZONE_PATTERN.fullmatch(timezone_value):
        raise _InvalidConfiguration("invalid timezone")

    worldwide = value.get("worldwide", False)
    exclude_worldwide = value.get("exclude_worldwide", False)
    if not isinstance(worldwide, bool) or not isinstance(exclude_worldwide, bool):
        raise _InvalidConfiguration("invalid worldwide flag")
    if worldwide and exclude_worldwide:
        raise _InvalidConfiguration("conflicting worldwide flags")
    if exclude_worldwide and not country:
        raise _InvalidConfiguration("exclude-worldwide requires country")

    seniority = _normalize_enum_list(
        value.get("seniority"), allowed=_SENIORITY_VALUES
    )
    employment_type = _normalize_enum_list(
        value.get("employment_type"), allowed=_EMPLOYMENT_TYPE_VALUES
    )
    company_slugs = _normalize_company_slugs(value.get("company_slugs"))

    sort = _profile_text(value.get("sort"), maximum=32)
    if sort and sort not in _SORT_VALUES:
        raise _InvalidConfiguration("invalid sort")

    if not any(
        (
            query,
            country,
            worldwide,
            exclude_worldwide,
            seniority,
            employment_type,
            company_slugs,
            timezone_value,
        )
    ):
        raise _InvalidConfiguration("unrestricted profile")

    return {
        "profile_id": profile_id,
        "query": query,
        "country": country,
        "worldwide": worldwide,
        "exclude_worldwide": exclude_worldwide,
        "seniority": seniority,
        "employment_type": employment_type,
        "company_slugs": company_slugs,
        "timezone": timezone_value,
        "sort": sort,
    }


def _load_query_profiles(path=None):
    profile_path = HIMALAYAS_QUERY_PROFILES_PATH if path is None else path
    try:
        payload = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _InvalidConfiguration("invalid query-profile file") from exc
    if not isinstance(payload, list) or len(payload) > HIMALAYAS_MAX_QUERY_PROFILES:
        raise _InvalidConfiguration("invalid query-profile collection")

    profiles = [_normalize_profile(value) for value in payload]
    profile_ids = [profile["profile_id"] for profile in profiles]
    if len(profile_ids) != len(set(profile_ids)):
        raise _InvalidConfiguration("duplicate profile id")
    return sorted(profiles, key=lambda profile: profile["profile_id"])


def _profile_params(profile, page):
    params = {"page": page}
    mappings = (
        ("query", "q"),
        ("country", "country"),
        ("timezone", "timezone"),
        ("sort", "sort"),
    )
    for internal_name, provider_name in mappings:
        if profile[internal_name]:
            params[provider_name] = profile[internal_name]
    if profile["worldwide"]:
        params["worldwide"] = "true"
    if profile["exclude_worldwide"]:
        params["exclude_worldwide"] = "true"
    if profile["seniority"]:
        params["seniority"] = ",".join(profile["seniority"])
    if profile["employment_type"]:
        params["employment_type"] = ",".join(profile["employment_type"])
    if profile["company_slugs"]:
        params["company"] = ",".join(profile["company_slugs"])
    return params


@retry_request(retries=SCRAPER_RETRY_ATTEMPTS, retry_status=_RETRY_STATUSES)
def _himalayas_get(url, **kwargs):
    kwargs.setdefault("timeout", SCRAPER_HTTP_TIMEOUT_SECONDS)
    return requests.get(url, **kwargs)


def _request_page(profile, page):
    return _himalayas_get(
        HIMALAYAS_SEARCH_API,
        params=_profile_params(profile, page),
        timeout=SCRAPER_HTTP_TIMEOUT_SECONDS,
        allow_redirects=False,
    )


def _response_json(response):
    content_type = str(getattr(response, "headers", {}).get("Content-Type", ""))
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type not in _JSON_MEDIA_TYPES and not media_type.endswith("+json"):
        raise _MalformedPayload("unexpected content type")

    content = getattr(response, "content", b"")
    if isinstance(content, str):
        content = content.encode("utf-8")
    if not isinstance(content, bytes) or len(content) > HIMALAYAS_MAX_RESPONSE_BYTES:
        raise _MalformedPayload("invalid response body")
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise _MalformedPayload("invalid JSON") from None
    if not isinstance(payload, dict):
        raise _MalformedPayload("unexpected root schema")
    return payload


def _strict_nonnegative_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _MalformedPayload(f"invalid {name}")
    return value


def _parse_page(response, page):
    payload = _response_json(response)
    _strict_nonnegative_int(payload.get("updatedAt"), "updated timestamp")
    items = payload.get("jobs")
    if not isinstance(items, list) or len(items) > HIMALAYAS_RESULTS_PER_PAGE:
        raise _MalformedPayload("invalid result items")

    offset = _strict_nonnegative_int(payload.get("offset"), "offset")
    limit = _strict_nonnegative_int(payload.get("limit"), "limit")
    total_count = _strict_nonnegative_int(payload.get("totalCount"), "total count")
    expected_offset = (page - 1) * HIMALAYAS_RESULTS_PER_PAGE
    if limit != HIMALAYAS_RESULTS_PER_PAGE or offset != expected_offset:
        raise _MalformedPayload("inconsistent pagination")
    if offset + len(items) > total_count:
        raise _MalformedPayload("impossible result count")
    has_more = offset + len(items) < total_count
    return items, has_more


def _resolve_now(now=None):
    value = now() if callable(now) else now
    if value is None:
        value = datetime.now(timezone.utc)
    if not isinstance(value, datetime):
        raise ValueError("now must be a datetime or callable")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _timestamp(value, *, now=None):
    current = _resolve_now(now)
    parsed = None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            numeric = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
        if not numeric.is_finite() or numeric < 0 or numeric != numeric.to_integral_value():
            return None
        integer = int(numeric)
        earliest_seconds = int(_EARLIEST_PLAUSIBLE_TIMESTAMP.timestamp())
        latest_seconds = int(
            (current + timedelta(days=_MAX_TIMESTAMP_FUTURE_DAYS)).timestamp()
        )
        if earliest_seconds <= integer <= latest_seconds:
            seconds = integer
        elif earliest_seconds * 1_000 <= integer <= latest_seconds * 1_000:
            seconds = integer / 1_000
        else:
            return None
        try:
            parsed = datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    elif isinstance(value, str):
        text = value.strip()
        if not text or len(text) > 64:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        parsed = parsed.astimezone(timezone.utc)
    else:
        return None

    latest = current + timedelta(days=_MAX_TIMESTAMP_FUTURE_DAYS)
    if parsed < _EARLIEST_PLAUSIBLE_TIMESTAMP or parsed > latest:
        return None
    normalized = parsed.isoformat().replace("+00:00", "Z")
    return normalized, parsed


def _canonical_url(value):
    if not isinstance(value, str):
        return ""
    raw = value.strip()
    if len(raw) > 2_048:
        return ""
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError:
        return ""
    lowered_path = parsed.path.lower()
    if (
        parsed.scheme != "https"
        or parsed.hostname != "himalayas.app"
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or parsed.query
        or parsed.fragment
        or not _JOB_PATH_PATTERN.fullmatch(parsed.path)
        or any(part in lowered_path for part in _PROHIBITED_URL_PATH_PARTS)
    ):
        return ""
    return raw


def _safe_logo_url(value):
    if not isinstance(value, str):
        return ""
    raw = value.strip()
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError:
        return ""
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or not parsed.path
        or parsed.query
        or parsed.fragment
        or any(part in parsed.path.lower() for part in _PROHIBITED_URL_PATH_PARTS)
    ):
        return ""
    return raw[:2_048]


def _plain_text(value):
    if not isinstance(value, str):
        return ""
    parser = _PlainTextParser()
    try:
        parser.feed(str(value or ""))
        parser.close()
    except Exception:
        return ""
    text = html.unescape(parser.text())
    text = _VISIBLE_URL_PATTERN.sub("", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n+", "\n", text).strip()
    text = "\n".join(
        line for line in text.splitlines() if not _APPLICATION_FLOW_PATTERN.search(line)
    ).strip()
    return text[:HIMALAYAS_MAX_DESCRIPTION_CHARS].rstrip()


def _ordered_text_list(value, *, dictionary_key=None, maximum=200):
    if not isinstance(value, list):
        return []
    rows = []
    for item in value[:_MAX_METADATA_LIST_ITEMS]:
        if dictionary_key is not None:
            if not isinstance(item, dict):
                continue
            item = item.get(dictionary_key)
        if not isinstance(item, str):
            continue
        clean = _clean_text(item, maximum=maximum)
        if clean and clean not in rows:
            rows.append(clean)
    return rows


def _country_from_code(value):
    if isinstance(value, bool) or not isinstance(value, str):
        return ""
    code = value.strip().upper()
    if len(code) != 2 or not code.isascii() or not code.isalpha():
        return ""
    country = pycountry.countries.get(alpha_2=code)
    return str(getattr(country, "name", "") or "").strip()


def _country_from_name(value):
    if isinstance(value, bool) or not isinstance(value, str):
        return ""
    name = _clean_text(value, maximum=201)
    if not name or len(name) > 200:
        return ""
    normalized = name.casefold()
    for country in pycountry.countries:
        known_names = {
            str(getattr(country, field, "") or "").strip().casefold()
            for field in ("name", "official_name", "common_name")
        }
        if normalized in known_names:
            return str(getattr(country, "name", "") or "").strip()
    return ""


def _country_from_slug(value):
    if isinstance(value, bool) or not isinstance(value, str):
        return ""
    slug = value.strip().lower()
    if (
        not slug
        or len(slug) > 200
        or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)
    ):
        return ""
    return _country_from_name(slug.replace("-", " "))


def _restriction_country(value):
    if isinstance(value, str):
        return _country_from_code(value) or _country_from_name(value)
    if not isinstance(value, dict):
        return ""
    return (
        _country_from_code(value.get("alpha2"))
        or _country_from_name(value.get("name"))
        or _country_from_slug(value.get("slug"))
    )


def _normalize_country_restrictions(value):
    if value is None:
        return [], False, False
    if not isinstance(value, list) or len(value) > _MAX_METADATA_LIST_ITEMS:
        return [], False, True

    countries = []
    worldwide = False
    malformed = False
    for restriction in value:
        if isinstance(restriction, str) and restriction.strip().lower() == "worldwide":
            worldwide = True
            continue
        country = _restriction_country(restriction)
        if not country:
            malformed = True
            continue
        if country not in countries:
            countries.append(country)
    return countries, worldwide, malformed


def _remote_locations(countries, *, worldwide=False):
    if countries:
        return [f"Remote, {country}" for country in countries]
    if worldwide:
        return ["Remote, Worldwide"]
    return ["Remote"]


def _decimal_string(value):
    if value is None or isinstance(value, bool):
        return ""
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return ""
    if not parsed.is_finite() or parsed < 0:
        return ""
    text = format(parsed, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _normalize_result_with_reason(item, *, now=None):
    if not isinstance(item, dict):
        return "malformed", None, "invalid_row"
    raw_guid = item.get("guid")
    raw_title = item.get("title")
    raw_company = item.get("companyName")
    guid = raw_guid.strip() if isinstance(raw_guid, str) else ""
    title = _clean_text(raw_title, maximum=1_000) if isinstance(raw_title, str) else ""
    company = (
        _clean_text(raw_company, maximum=1_000)
        if isinstance(raw_company, str)
        else ""
    )
    publication = _timestamp(item.get("pubDate"), now=now)
    expiry = _timestamp(item.get("expiryDate"), now=now)
    url = _canonical_url(item.get("applicationLink"))
    required_fields = (
        ("invalid_guid", bool(_GUID_PATTERN.fullmatch(guid))),
        ("invalid_title", bool(title)),
        ("invalid_company", bool(company)),
        ("invalid_publication_timestamp", publication is not None),
        ("invalid_expiry_timestamp", expiry is not None),
        ("invalid_application_link", bool(url)),
    )
    for reason, valid in required_fields:
        if not valid:
            return "malformed", None, reason

    current = _resolve_now(now)
    publication_text, _publication_datetime = publication
    expiry_text, expiry_datetime = expiry
    if expiry_datetime <= current:
        return "expired", None, ""

    countries, worldwide_restriction, malformed_restrictions = (
        _normalize_country_restrictions(item.get("locationRestrictions"))
    )
    timezones = _ordered_text_list(item.get("timezoneRestrictions"), maximum=32)
    locations = _remote_locations(countries, worldwide=worldwide_restriction)

    metadata = {
        "expiry_date": expiry_text,
        "remote": True,
        "worldwide": (
            worldwide_restriction
            or not countries and not timezones and not malformed_restrictions
        ),
        "provider_attribution_required": True,
        "provider_attribution_label": "Himalayas",
        "provider_attribution_url": url,
    }
    description = _plain_text(item.get("description"))
    if description:
        metadata["description"] = description
    if malformed_restrictions:
        metadata["location_restrictions_unresolved"] = True

    company_slug = item.get("companySlug")
    if isinstance(company_slug, str):
        company_slug = company_slug.strip()
        if _COMPANY_SLUG_PATTERN.fullmatch(company_slug):
            metadata["company_slug"] = company_slug
    employment_type = item.get("employmentType")
    if isinstance(employment_type, str) and employment_type in _EMPLOYMENT_TYPE_VALUES:
        metadata["employment_type"] = employment_type
    currency = item.get("currency")
    if isinstance(currency, str) and _CURRENCY_PATTERN.fullmatch(currency):
        metadata["currency"] = currency
    salary_period = item.get("salaryPeriod")
    if isinstance(salary_period, str) and salary_period in _SALARY_PERIOD_VALUES:
        metadata["salary_period"] = salary_period

    logo_url = _safe_logo_url(item.get("companyLogo"))
    if logo_url:
        metadata["company_logo_url"] = logo_url

    seniority = [
        value
        for value in _ordered_text_list(item.get("seniority"), maximum=100)
        if value in _SENIORITY_VALUES
    ]
    list_fields = (
        ("seniority", seniority, 100),
        ("categories", item.get("categories"), 200),
        ("country_restrictions", countries, 200),
        ("timezone_restrictions", timezones, 32),
    )
    for key, value, maximum in list_fields:
        rows = _ordered_text_list(value, maximum=maximum)
        if rows:
            metadata[key] = rows

    minimum = _decimal_string(item.get("minSalary"))
    maximum = _decimal_string(item.get("maxSalary"))
    if minimum and maximum and Decimal(minimum) > Decimal(maximum):
        minimum = ""
        maximum = ""
    if minimum:
        metadata["salary_minimum"] = minimum
    if maximum:
        metadata["salary_maximum"] = maximum
    try:
        job = Job(
            company=company,
            title=title,
            location=locations,
            url=url,
            source="himalayas",
            posted_at=publication_text,
            job_id=f"himalayas_{guid}",
            meta=metadata,
        ).to_dict()
    except Exception:
        return "malformed", None, "invalid_job"
    return "usable", job, ""


def _normalize_result(item, *, now=None):
    state, job, _reason = _normalize_result_with_reason(item, now=now)
    return state, job


def _failed_outcome(profile_id, reason, *, page_count=0, raw_job_count=0):
    return AcquisitionOutcome(
        f"himalayas:{profile_id}",
        AcquisitionStatus.FAILED,
        reason=reason,
        page_count=page_count,
        raw_job_count=raw_job_count,
    )


def _page_guid_evidence(items):
    evidence = []
    for item in items:
        raw_guid = item.get("guid") if isinstance(item, dict) else None
        guid = raw_guid.strip() if isinstance(raw_guid, str) else ""
        evidence.append(guid if _GUID_PATTERN.fullmatch(guid) else "")
    return tuple(evidence)


def _log_row_diagnostics(profile_id, diagnostics):
    for reason in sorted(diagnostics):
        count = diagnostics[reason]
        if count:
            logger.info(
                "himalayas_event profile=%s row_normalization_%s_count=%s",
                profile_id,
                reason,
                count,
            )


def _incomplete_outcome(
    profile_id,
    jobs,
    reason,
    *,
    page_count,
    raw_job_count,
    diagnostics,
):
    _log_row_diagnostics(profile_id, diagnostics)
    if jobs:
        return AcquisitionOutcome(
            f"himalayas:{profile_id}",
            AcquisitionStatus.PARTIAL,
            tuple(jobs),
            reason=reason,
            page_count=page_count,
            raw_job_count=raw_job_count,
        )
    return _failed_outcome(
        profile_id,
        reason,
        page_count=page_count,
        raw_job_count=raw_job_count,
    )


def _fetch_profile_outcome(profile, *, now=None):
    profile_id = profile["profile_id"]
    jobs = []
    malformed_count = 0
    expired_count = 0
    raw_job_count = 0
    parsed_page_count = 0
    row_diagnostics = {}
    page_fingerprints = set()
    seen_guids = set()
    incomplete_reason = ""

    for page in range(1, HIMALAYAS_MAX_PAGES_PER_PROFILE + 1):
        try:
            response = _request_page(profile, page)
        except Exception:
            reason = "transport_error" if page == 1 else "pagination_interrupted"
            return _incomplete_outcome(
                profile_id,
                jobs,
                reason,
                page_count=parsed_page_count,
                raw_job_count=raw_job_count,
                diagnostics=row_diagnostics,
            )

        if response is None or getattr(response, "status_code", None) != 200:
            reason = "non_200_response" if page == 1 else "pagination_interrupted"
            return _incomplete_outcome(
                profile_id,
                jobs,
                reason,
                page_count=parsed_page_count,
                raw_job_count=raw_job_count,
                diagnostics=row_diagnostics,
            )

        try:
            items, has_more = _parse_page(response, page)
        except _MalformedPayload:
            reason = "malformed_payload" if page == 1 else "pagination_interrupted"
            return _incomplete_outcome(
                profile_id,
                jobs,
                reason,
                page_count=parsed_page_count,
                raw_job_count=raw_job_count,
                diagnostics=row_diagnostics,
            )

        parsed_page_count += 1
        raw_job_count += len(items)
        guid_evidence = _page_guid_evidence(items)
        fingerprint = (len(items), guid_evidence)
        if fingerprint in page_fingerprints:
            logger.info("himalayas_event profile=%s repeated_page=true", profile_id)
            incomplete_reason = "pagination_no_progress"
            break
        page_fingerprints.add(fingerprint)

        valid_page_guids = {guid for guid in guid_evidence if guid}
        if items and not valid_page_guids.difference(seen_guids) and has_more:
            logger.info("himalayas_event profile=%s no_new_guids=true", profile_id)
            incomplete_reason = "pagination_no_progress"
            break
        seen_guids.update(valid_page_guids)

        for item in items:
            state, job, row_reason = _normalize_result_with_reason(item, now=now)
            if state == "malformed":
                malformed_count += 1
                row_diagnostics[row_reason] = row_diagnostics.get(row_reason, 0) + 1
            elif state == "expired":
                expired_count += 1
            else:
                jobs.append(job)

        if not has_more:
            break
        if page == HIMALAYAS_MAX_PAGES_PER_PROFILE:
            logger.info("himalayas_event bounded_page_cap_reached=true")
            incomplete_reason = "pagination_limit_reached"

    if incomplete_reason:
        return _incomplete_outcome(
            profile_id,
            jobs,
            incomplete_reason,
            page_count=parsed_page_count,
            raw_job_count=raw_job_count,
            diagnostics=row_diagnostics,
        )

    company = f"himalayas:{profile_id}"
    _log_row_diagnostics(profile_id, row_diagnostics)
    if jobs:
        status = AcquisitionStatus.PARTIAL if malformed_count else AcquisitionStatus.SUCCESS
        return AcquisitionOutcome(
            company,
            status,
            tuple(jobs),
            reason="parse_error" if malformed_count else "",
            page_count=parsed_page_count,
            raw_job_count=raw_job_count,
        )
    if malformed_count:
        return _failed_outcome(
            profile_id,
            "parse_error",
            page_count=parsed_page_count,
            raw_job_count=raw_job_count,
        )
    if raw_job_count == expired_count or raw_job_count == 0:
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.EMPTY,
            page_count=parsed_page_count,
            raw_job_count=raw_job_count,
        )
    return _failed_outcome(
        profile_id,
        "parse_error",
        page_count=parsed_page_count,
        raw_job_count=raw_job_count,
    )


def scrape_all_himalayas():
    try:
        profiles = _load_query_profiles()
    except _InvalidConfiguration:
        logger.warning("himalayas_event invalid_query_profiles=true")
        return []
    if not profiles:
        return []

    jobs = []
    for profile in profiles:
        outcome = observe_acquisition(
            "himalayas",
            lambda profile=profile: _fetch_profile_outcome(profile),
            schedule_on_success=False,
            company=f"himalayas:{profile['profile_id']}",
        )
        jobs.extend(outcome.jobs)
    return jobs
