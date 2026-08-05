from __future__ import annotations

import html
import json
import os
import re
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from models.job import Job
from src.config.consts import (
    SCRAPER_HTTP_TIMEOUT_SECONDS,
    USAJOBS_DATE_POSTED_DAYS,
    USAJOBS_MAX_DESCRIPTION_CHARS,
    USAJOBS_MAX_PAGES_PER_PROFILE,
    USAJOBS_MAX_QUERY_PROFILES,
    USAJOBS_MAX_RESPONSE_BYTES,
    USAJOBS_QUERY_PROFILES_PATH,
    USAJOBS_RESULTS_PER_PAGE,
    USAJOBS_SEARCH_API,
)
from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.utils.http_retry import http_get
from src.utils.logging import get_logger
from src.utils.pipeline_metrics import observe_acquisition

logger = get_logger("usajobs")

_PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_CONTROL_NUMBER_PATTERN = re.compile(r"^[0-9]{1,32}$")
_ORGANIZATION_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{1,16}$")
_JOB_CATEGORY_CODE_PATTERN = re.compile(r"^[0-9]{4}$")
_VISIBLE_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_APPLICATION_FLOW_PATTERN = re.compile(
    r"\b(?:how to apply|apply (?:at|now|online|through|via)|"
    r"submit(?: your| a)? (?:application|resume)|upload(?: your| a)? resume|"
    r"application form|candidate portal|resume upload)\b",
    re.IGNORECASE,
)
_JSON_MEDIA_TYPES = frozenset({"application/json", "text/json"})
_PUBLIC_HOSTS = frozenset({"usajobs.gov", "www.usajobs.gov"})
_PUBLIC_AUTHORITIES = frozenset(
    {
        "usajobs.gov",
        "www.usajobs.gov",
        "usajobs.gov:443",
        "www.usajobs.gov:443",
    }
)
_PROHIBITED_URL_PATH_PARTS = (
    "/apply",
    "/application",
    "/candidate",
    "/resume",
    "/account",
)
_ALLOWED_PROFILE_KEYS = frozenset(
    {
        "profile_id",
        "keyword",
        "location_name",
        "organization_codes",
        "job_category_codes",
        "remote_only",
    }
)
_DESCRIPTION_BLOCK_TAGS = frozenset(
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
_DESCRIPTION_SUPPRESSED_TAGS = frozenset(
    {"button", "form", "script", "select", "style", "textarea"}
)


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
        elif safe_tag in _DESCRIPTION_SUPPRESSED_TAGS:
            self._suppressed_depth = 1
        elif safe_tag in _DESCRIPTION_BLOCK_TAGS:
            self._parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if not self._suppressed_depth and str(tag or "").lower() in _DESCRIPTION_BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if self._suppressed_depth:
            self._suppressed_depth -= 1
        elif str(tag or "").lower() in _DESCRIPTION_BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if not self._suppressed_depth and data:
            self._parts.append(data)

    def text(self):
        return "".join(self._parts)


def _clean_text(value, *, maximum=10_000):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:maximum].rstrip()


def _normalized_codes(value, *, pattern, maximum_items=20):
    if value is None:
        return ()
    if not isinstance(value, list) or len(value) > maximum_items:
        raise _InvalidConfiguration("invalid profile code collection")
    values = []
    for item in value:
        code = str(item or "").strip()
        if not pattern.fullmatch(code):
            raise _InvalidConfiguration("invalid profile code")
        canonical = code.upper()
        if canonical not in values:
            values.append(canonical)
    return tuple(sorted(values))


def _normalize_profile(value):
    if not isinstance(value, dict) or set(value) - _ALLOWED_PROFILE_KEYS:
        raise _InvalidConfiguration("invalid profile object")

    profile_id = str(value.get("profile_id") or "").strip()
    if not _PROFILE_ID_PATTERN.fullmatch(profile_id):
        raise _InvalidConfiguration("invalid profile id")

    keyword = _clean_text(value.get("keyword"), maximum=200)
    location_name = _clean_text(value.get("location_name"), maximum=200)
    organization_codes = _normalized_codes(
        value.get("organization_codes"),
        pattern=_ORGANIZATION_CODE_PATTERN,
    )
    job_category_codes = _normalized_codes(
        value.get("job_category_codes"),
        pattern=_JOB_CATEGORY_CODE_PATTERN,
    )

    remote_only = value.get("remote_only", False)
    if not isinstance(remote_only, bool):
        raise _InvalidConfiguration("invalid remote-only value")
    if not any(
        (keyword, location_name, organization_codes, job_category_codes, remote_only)
    ):
        raise _InvalidConfiguration("unrestricted profile")

    return {
        "profile_id": profile_id,
        "keyword": keyword,
        "location_name": location_name,
        "organization_codes": organization_codes,
        "job_category_codes": job_category_codes,
        "remote_only": remote_only,
    }


def _load_query_profiles(path=None):
    profile_path = USAJOBS_QUERY_PROFILES_PATH if path is None else path
    try:
        payload = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _InvalidConfiguration("invalid query-profile file") from exc
    if not isinstance(payload, list) or len(payload) > USAJOBS_MAX_QUERY_PROFILES:
        raise _InvalidConfiguration("invalid query-profile collection")

    profiles = [_normalize_profile(value) for value in payload]
    profile_ids = [profile["profile_id"] for profile in profiles]
    if len(profile_ids) != len(set(profile_ids)):
        raise _InvalidConfiguration("duplicate profile id")
    return sorted(profiles, key=lambda profile: profile["profile_id"])


def _profile_params(profile, page):
    params = {
        "WhoMayApply": "Public",
        "Fields": "Full",
        "DatePosted": USAJOBS_DATE_POSTED_DAYS,
        "ResultsPerPage": USAJOBS_RESULTS_PER_PAGE,
        "Page": page,
    }
    if profile["keyword"]:
        params["Keyword"] = profile["keyword"]
    if profile["location_name"]:
        params["LocationName"] = profile["location_name"]
    if profile["organization_codes"]:
        params["Organization"] = ";".join(profile["organization_codes"])
    if profile["job_category_codes"]:
        params["JobCategoryCode"] = ";".join(profile["job_category_codes"])
    if profile["remote_only"]:
        params["RemoteIndicator"] = "True"
    return params


def _request_page(profile, page, api_key, user_agent_email):
    return http_get(
        USAJOBS_SEARCH_API,
        headers={
            "Host": "data.usajobs.gov",
            "User-Agent": user_agent_email,
            "Authorization-Key": api_key,
        },
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
    if not isinstance(content, bytes) or len(content) > USAJOBS_MAX_RESPONSE_BYTES:
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


def _usajobs_number_of_pages(value):
    maximum_provider_pages = 10_000 // USAJOBS_RESULTS_PER_PAGE
    if isinstance(value, bool):
        raise _MalformedPayload("invalid page count")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        if len(value) > len(str(maximum_provider_pages)):
            raise _MalformedPayload("page count exceeds result window")
        parsed = int(value)
    else:
        raise _MalformedPayload("invalid page count")
    if parsed < 0:
        raise _MalformedPayload("invalid page count")
    if parsed > maximum_provider_pages:
        raise _MalformedPayload("page count exceeds result window")
    return parsed


def _parse_page(response, page):
    payload = _response_json(response)
    search_result = payload.get("SearchResult")
    if not isinstance(search_result, dict):
        raise _MalformedPayload("missing search result")
    items = search_result.get("SearchResultItems")
    if not isinstance(items, list) or len(items) > USAJOBS_RESULTS_PER_PAGE:
        raise _MalformedPayload("invalid result items")

    returned_count = _strict_nonnegative_int(
        search_result.get("SearchResultCount"), "result count"
    )
    total_count = _strict_nonnegative_int(
        search_result.get("SearchResultCountAll"), "total count"
    )
    user_area = search_result.get("UserArea")
    if not isinstance(user_area, dict):
        raise _MalformedPayload("missing pagination metadata")
    number_of_pages = _usajobs_number_of_pages(user_area.get("NumberOfPages"))

    if returned_count != len(items) or returned_count > total_count:
        raise _MalformedPayload("inconsistent result counts")
    maximum_provider_pages = 10_000 // USAJOBS_RESULTS_PER_PAGE
    if number_of_pages > maximum_provider_pages:
        raise _MalformedPayload("page count exceeds result window")
    if total_count == 0 and number_of_pages not in {0, 1}:
        raise _MalformedPayload("impossible empty pagination")
    if total_count and number_of_pages < 1:
        raise _MalformedPayload("impossible pagination")
    if number_of_pages and page > number_of_pages:
        raise _MalformedPayload("requested page exceeds page count")
    if page < number_of_pages and returned_count != USAJOBS_RESULTS_PER_PAGE:
        raise _MalformedPayload("incomplete intermediate page")
    return items, number_of_pages


def _control_number(value):
    if isinstance(value, bool):
        return ""
    text = str(value or "").strip()
    if not _CONTROL_NUMBER_PATTERN.fullmatch(text):
        return ""
    return str(int(text))


def _canonical_url(value, control_number):
    raw = str(value or "").strip()
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return ""
    try:
        port = parsed.port
    except ValueError:
        return ""
    lowered_path = parsed.path.lower()
    if (
        parsed.scheme != "https"
        or parsed.hostname not in _PUBLIC_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.netloc.lower() not in _PUBLIC_AUTHORITIES
        or port not in {None, 443}
        or not parsed.path
        or parsed.query
        or parsed.fragment
        or any(part in lowered_path for part in _PROHIBITED_URL_PATH_PARTS)
        or control_number not in parsed.path.split("/")
    ):
        return ""
    return raw


def _plain_text(value):
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
        line
        for line in text.splitlines()
        if not _APPLICATION_FLOW_PATTERN.search(line)
    ).strip()
    return text[:USAJOBS_MAX_DESCRIPTION_CHARS].rstrip()


def _details(descriptor):
    user_area = descriptor.get("UserArea")
    if not isinstance(user_area, dict):
        return {}
    details = user_area.get("Details")
    return details if isinstance(details, dict) else {}


def _description(descriptor):
    details = _details(descriptor)
    sections = (
        ("Summary", details.get("JobSummary")),
        ("Duties", details.get("MajorDuties")),
        ("Qualifications", descriptor.get("QualificationSummary")),
        ("Education", details.get("Education")),
        ("Requirements", details.get("Requirements")),
        ("Evaluations", details.get("Evaluations")),
        ("Other job information", details.get("OtherInformation")),
    )
    parts = []
    for heading, raw_value in sections:
        body = _plain_text(raw_value)
        if body:
            parts.append(f"{heading}\n{body}")
    return "\n\n".join(parts)[:USAJOBS_MAX_DESCRIPTION_CHARS].rstrip()


def _locations(descriptor):
    values = []
    raw_locations = descriptor.get("PositionLocation")
    if isinstance(raw_locations, list):
        for location in raw_locations:
            if not isinstance(location, dict):
                continue
            name = _clean_text(location.get("LocationName"), maximum=500)
            if name and name not in values:
                values.append(name)
    if not values:
        fallback = _clean_text(descriptor.get("PositionLocationDisplay"), maximum=500)
        if fallback:
            values.append(fallback)
    return values


def _timestamp(value):
    text = str(value or "").strip()
    if not text or len(text) > 64:
        return ""
    try:
        from datetime import datetime

        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return ""
    return text


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


def _named_code_list(value):
    if not isinstance(value, list):
        return []
    rows = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name = _clean_text(item.get("Name"), maximum=500)
        code = _clean_text(item.get("Code"), maximum=100)
        row = {}
        if name:
            row["name"] = name
        if code:
            row["code"] = code
        if row and row not in rows:
            rows.append(row)
    return rows


def _metadata(descriptor, *, remote_only):
    details = _details(descriptor)
    metadata = {}

    description = _description(descriptor)
    if description:
        metadata["description"] = description
        metadata["description_text"] = description

    scalar_fields = (
        ("agency", descriptor.get("OrganizationName")),
        ("department", descriptor.get("DepartmentName")),
        ("subagency", details.get("SubAgencyName")),
        ("announcement_number", descriptor.get("PositionID")),
    )
    for key, value in scalar_fields:
        clean = _clean_text(value, maximum=1_000)
        if clean:
            metadata[key] = clean

    timestamps = (
        ("publication_date", descriptor.get("PublicationStartDate")),
        ("opening_date", descriptor.get("PositionStartDate")),
        ("closing_date", descriptor.get("PositionEndDate")),
        ("application_close_date", descriptor.get("ApplicationCloseDate")),
    )
    for key, value in timestamps:
        clean = _timestamp(value)
        if clean:
            metadata[key] = clean

    list_fields = (
        ("occupational_categories", descriptor.get("JobCategory")),
        ("grades", descriptor.get("JobGrade")),
        ("position_schedules", descriptor.get("PositionSchedule")),
        ("offering_types", descriptor.get("PositionOfferingType")),
    )
    for key, value in list_fields:
        rows = _named_code_list(value)
        if rows:
            metadata[key] = rows

    who_may_apply = details.get("WhoMayApply")
    if isinstance(who_may_apply, dict):
        rows = _named_code_list([who_may_apply])
        if rows:
            metadata["public_eligibility"] = rows[0]

    remuneration = descriptor.get("PositionRemuneration")
    if isinstance(remuneration, list):
        for row in remuneration:
            if not isinstance(row, dict):
                continue
            minimum = _decimal_string(row.get("MinimumRange"))
            maximum = _decimal_string(row.get("MaximumRange"))
            interval = _clean_text(row.get("RateIntervalCode"), maximum=100)
            if minimum and maximum and Decimal(minimum) > Decimal(maximum):
                minimum = ""
                maximum = ""
            if minimum:
                metadata["salary_minimum"] = minimum
            if maximum:
                metadata["salary_maximum"] = maximum
            if interval:
                metadata["salary_rate_interval"] = interval
            if minimum or maximum or interval:
                break

    if remote_only:
        metadata["remote"] = True
    return metadata


def _normalize_result(item, *, remote_only):
    if not isinstance(item, dict):
        return None
    control_number = _control_number(item.get("MatchedObjectId"))
    descriptor = item.get("MatchedObjectDescriptor")
    if not control_number or not isinstance(descriptor, dict):
        return None

    title = _clean_text(descriptor.get("PositionTitle"), maximum=1_000)
    company = _clean_text(descriptor.get("OrganizationName"), maximum=1_000)
    url = _canonical_url(descriptor.get("PositionURI"), control_number)
    if not title or not company or not url:
        return None

    try:
        return Job(
            company=company,
            title=title,
            location=_locations(descriptor),
            url=url,
            source="usajobs",
            posted_at=_timestamp(descriptor.get("PublicationStartDate")) or None,
            job_id=f"usajobs_{control_number}",
            meta=_metadata(descriptor, remote_only=remote_only),
        ).to_dict()
    except Exception:
        return None


def _failed_outcome(profile_id, reason, *, page_count=0, raw_job_count=0):
    return AcquisitionOutcome(
        f"usajobs:{profile_id}",
        AcquisitionStatus.FAILED,
        reason=reason,
        page_count=page_count,
        raw_job_count=raw_job_count,
    )


def _fetch_profile_outcome(profile, api_key, user_agent_email):
    profile_id = profile["profile_id"]
    jobs = []
    malformed_count = 0
    raw_job_count = 0
    parsed_page_count = 0

    for page in range(1, USAJOBS_MAX_PAGES_PER_PROFILE + 1):
        try:
            response = _request_page(profile, page, api_key, user_agent_email)
        except Exception:
            if jobs:
                return AcquisitionOutcome(
                    f"usajobs:{profile_id}",
                    AcquisitionStatus.PARTIAL,
                    tuple(jobs),
                    reason="pagination_interrupted",
                    page_count=parsed_page_count,
                    raw_job_count=raw_job_count,
                )
            reason = "transport_error" if page == 1 else "pagination_interrupted"
            return _failed_outcome(
                profile_id,
                reason,
                page_count=parsed_page_count,
                raw_job_count=raw_job_count,
            )

        if response is None or getattr(response, "status_code", None) != 200:
            if jobs:
                return AcquisitionOutcome(
                    f"usajobs:{profile_id}",
                    AcquisitionStatus.PARTIAL,
                    tuple(jobs),
                    reason="pagination_interrupted",
                    page_count=parsed_page_count,
                    raw_job_count=raw_job_count,
                )
            reason = "non_200_response" if page == 1 else "pagination_interrupted"
            return _failed_outcome(
                profile_id,
                reason,
                page_count=parsed_page_count,
                raw_job_count=raw_job_count,
            )

        try:
            items, number_of_pages = _parse_page(response, page)
        except _MalformedPayload:
            if jobs:
                return AcquisitionOutcome(
                    f"usajobs:{profile_id}",
                    AcquisitionStatus.PARTIAL,
                    tuple(jobs),
                    reason="pagination_interrupted",
                    page_count=parsed_page_count,
                    raw_job_count=raw_job_count,
                )
            reason = "malformed_payload" if page == 1 else "pagination_interrupted"
            return _failed_outcome(
                profile_id,
                reason,
                page_count=parsed_page_count,
                raw_job_count=raw_job_count,
            )

        parsed_page_count += 1
        raw_job_count += len(items)
        for item in items:
            job = _normalize_result(item, remote_only=profile["remote_only"])
            if job is None:
                malformed_count += 1
            else:
                jobs.append(job)

        if page >= number_of_pages or not items:
            break
        if page == USAJOBS_MAX_PAGES_PER_PROFILE:
            logger.info("usajobs_event bounded_page_cap_reached=true")

    company = f"usajobs:{profile_id}"
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
    if raw_job_count:
        return _failed_outcome(
            profile_id,
            "parse_error",
            page_count=parsed_page_count,
            raw_job_count=raw_job_count,
        )
    return AcquisitionOutcome(
        company,
        AcquisitionStatus.EMPTY,
        page_count=parsed_page_count,
        raw_job_count=0,
    )


def scrape_all_usajobs():
    try:
        profiles = _load_query_profiles()
    except _InvalidConfiguration:
        logger.warning("usajobs_event invalid_query_profiles=true")
        return []
    if not profiles:
        return []

    api_key = str(os.environ.get("USAJOBS_API_KEY", "") or "").strip()
    user_agent_email = str(
        os.environ.get("USAJOBS_USER_AGENT_EMAIL", "") or ""
    ).strip()
    if not api_key or not user_agent_email:
        logger.warning("usajobs_event required_credentials_missing=true")
        return []

    jobs = []
    for profile in profiles:
        outcome = observe_acquisition(
            "usajobs",
            lambda profile=profile: _fetch_profile_outcome(
                profile,
                api_key,
                user_agent_email,
            ),
            schedule_on_success=False,
            company=f"usajobs:{profile['profile_id']}",
        )
        jobs.extend(outcome.jobs)
    return jobs
