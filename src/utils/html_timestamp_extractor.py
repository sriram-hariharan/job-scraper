import html as html_module
import json
import re


_JSONLD_SCRIPT_RE = re.compile(
    r"<script[^>]*type\s*=\s*['\"]application/ld\+json['\"][^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _jobposting_type(value):
    values = value if isinstance(value, list) else [value]
    return any(_clean_text(item).lower() == "jobposting" for item in values)


def _jobposting_nodes(value):
    if isinstance(value, dict):
        if _jobposting_type(value.get("@type")):
            yield value
        for nested in value.values():
            yield from _jobposting_nodes(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _jobposting_nodes(nested)


def _jsonld_payloads(page_html):
    for block in _JSONLD_SCRIPT_RE.findall(str(page_html or "")):
        try:
            yield json.loads(html_module.unescape(block.strip()))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue


def _named_value(value):
    if isinstance(value, dict):
        value = value.get("name") or value.get("value")
    return _clean_text(value)


def _address_location(value):
    if not isinstance(value, dict):
        return ""
    address = value.get("address")
    if not isinstance(address, dict):
        address = value
    parts = [
        _named_value(address.get(field))
        for field in ("addressLocality", "addressRegion", "addressCountry")
    ]
    return ", ".join(part for part in parts if part)


def _location_rows(value):
    values = value if isinstance(value, list) else [value]
    rows = []
    for item in values:
        location = _address_location(item)
        if location and location not in rows:
            rows.append(location)
    return rows


def extract_jsonld_jobposting_metadata(page_html):
    """Return bounded, description-free metadata from the first JobPosting node."""
    empty = {
        "posted_at": None,
        "locations": [],
        "job_location_type": "",
        "applicant_location_requirements": [],
    }

    for payload in _jsonld_payloads(page_html):
        for node in _jobposting_nodes(payload):
            posted_at = node.get("datePosted") or node.get("datePublished") or None
            locations = _location_rows(node.get("jobLocation"))
            requirements = _location_rows(node.get("applicantLocationRequirements"))
            if not requirements:
                raw_requirements = node.get("applicantLocationRequirements")
                requirement_values = (
                    raw_requirements
                    if isinstance(raw_requirements, list)
                    else [raw_requirements]
                )
                for requirement in requirement_values:
                    name = _named_value(requirement)
                    if name and name not in requirements:
                        requirements.append(name)

            location_type = _clean_text(node.get("jobLocationType"))
            if location_type.upper() == "TELECOMMUTE":
                remote_locations = [
                    f"Remote, {requirement}"
                    for requirement in requirements
                    if requirement
                ]
                if remote_locations:
                    locations = remote_locations
                elif not locations:
                    locations = ["Remote"]

            return {
                "posted_at": posted_at,
                "locations": locations,
                "job_location_type": location_type,
                "applicant_location_requirements": requirements,
            }

    return empty


def extract_jsonld_dateposted(page_html):
    for payload in _jsonld_payloads(page_html):
        posted_at = find_dateposted(payload)
        if posted_at:
            return posted_at
    return None


def find_dateposted(obj):
    for node in _jobposting_nodes(obj):
        posted_at = node.get("datePosted") or node.get("datePublished")
        if posted_at:
            return posted_at
    return None
