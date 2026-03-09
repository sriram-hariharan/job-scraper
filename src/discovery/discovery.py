from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json
from src.discovery.ats_detector import (
    fetch_career_page,
    fetch_career_subdomain,
    extract_links_from_html,
    detect_ats_from_links,
    detect_ats_from_html,
    extract_greenhouse_slug,
    extract_ashby_slug,
    extract_lever_slug,
    extract_workday_url,
    extract_workable_slug,
    extract_jobvite_slug,
    check_greenhouse,
    check_ashby,
    slug_from_domain,
    extract_lever_slug_from_domain,
    extract_workday_board_url,
    detect_ats_from_redirect
)
from src.config.consts import SUPPORTED_ATS
from tqdm import tqdm

CACHE_PATH = "data/ats_cache.json"

def load_cache():

    if not os.path.exists(CACHE_PATH):
        return {}

    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache):

    os.makedirs("data", exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)

def extract_slug(link, html, link_prefix, html_extractor):
    
    slug = None

    if link and link_prefix in link:
        try:
            slug = link.split(link_prefix)[1].split("/")[0].split("?")[0]
        except:
            slug = None
    if not slug:
        slug = html_extractor(html)

    return slug
    
def detect_ats_for_domain(domain: str):

    result = {
        "greenhouse": None,
        "ashby": None,
        "lever": None,
        "workday": None,
        "workable": None,
        "jobvite": None
    }

    slug = slug_from_domain(domain)

    # --- FAST ATS DETECTION ---
    try:
        if slug and check_greenhouse(slug):
            result["greenhouse"] = slug
            return result
    except:
        pass

    try:
        if slug and check_ashby(slug):
            result["ashby"] = slug
            return result
    except:
        pass

    try:
        lever_slug = extract_lever_slug_from_domain(domain)
        if lever_slug:
            result["lever"] = lever_slug
            return result
    except:
        pass

    try:
        wd_url = extract_workday_board_url(domain)
        if wd_url:
            result["workday"] = wd_url
            return result
    except:
        pass
    
    # redirect detection
    try:
        ats, value = detect_ats_from_redirect(domain)
        if ats:
            result[ats] = value
            return result
    except:
        pass
    
    # fetch career page once
    html = fetch_career_page(domain)

    if not html:
        html = fetch_career_subdomain(domain)

    links = []
    ats = None
    link = None

    if html:
        links = extract_links_from_html(html)
        ats, link = detect_ats_from_links(links)
        if not ats:
            ats = detect_ats_from_html(html)

        try:

            if ats == "greenhouse":
                slug = extract_slug(
                    link,
                    html,
                    "boards.greenhouse.io/",
                    extract_greenhouse_slug
                )

                if slug and check_greenhouse(slug):
                    result["greenhouse"] = slug

            elif ats == "ashby":
                slug = extract_slug(
                    link,
                    html,
                    "jobs.ashbyhq.com/",
                    extract_ashby_slug
                )

                if slug and check_ashby(slug):
                    result["ashby"] = slug


            elif ats == "lever":
                slug = extract_slug(
                    link,
                    html,
                    "lever.co/",
                    extract_lever_slug
                )

                if slug:
                    result["lever"] = slug


            elif ats == "workday":
                wd_url = None

                if link and "myworkdayjobs.com" in link:
                    wd_url = link.split("?")[0]

                if not wd_url:
                    wd_url = extract_workday_url(html)

                if wd_url:
                    result["workday"] = wd_url


            elif ats == "workable":
                slug = extract_slug(
                    link,
                    html,
                    "apply.workable.com/",
                    extract_workable_slug
                )

                if slug:
                    result["workable"] = slug


            elif ats == "jobvite":
                slug = extract_slug(
                    link,
                    html,
                    "jobs.jobvite.com/",
                    extract_jobvite_slug
                )

                if slug:
                    result["jobvite"] = slug

        except:
            pass

        if not any(result.values()):
            slug = slug_from_domain(domain)

            try:
                if slug and check_greenhouse(slug):
                    result["greenhouse"] = slug
                    return result
            except:
                pass

            try:
                if slug and check_ashby(slug):
                    result["ashby"] = slug
                    return result
            except:
                pass

            try:
                lever_slug = extract_lever_slug_from_domain(domain)
                if lever_slug:
                    result["lever"] = lever_slug
                    return result
            except:
                pass

            try:
                wd_url = extract_workday_board_url(domain)
                if wd_url:
                    result["workday"] = wd_url
                    return result
            except:
                pass

    return result


def discover_from_domains(domains: List[str]) -> Dict[str, List[str]]:
    
    cache = load_cache()

    buckets: Dict[str, List[str]] = {ats: [] for ats in SUPPORTED_ATS}

    cleaned = []
    seen = set()

    for domain in domains:

        if not domain:
            continue

        value = domain.strip().lower()

        if not value or value in seen:
            continue

        seen.add(value)
        cleaned.append(value)
    
    to_detect = []
    cached_results = []

    for domain in cleaned:
        if domain in cache:
            cached_results.append(cache[domain])
        else:
            to_detect.append(domain)

    # parallel ATS detection
    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:

        futures = {
            executor.submit(detect_ats_for_domain, domain): domain
            for domain in to_detect
        }

        for future in tqdm(
        as_completed(futures),
        total=len(futures),
        desc="ATS discovery",
        unit="domain"
        ):

            domain = futures[future]

            try:
                result = future.result(timeout=5)
            except Exception:
                result = {
                    "greenhouse": None,
                    "ashby": None,
                    "lever": None,
                    "workday": None,
                    "workable": None,
                    "jobvite": None
                }

            cache[domain] = result
            results.append(result)

    # merge results
    all_results = cached_results + results
    for r in all_results:

        if r["greenhouse"]:
            buckets["greenhouse"].append(r["greenhouse"])

        if r["ashby"]:
            buckets["ashby"].append(r["ashby"])

        if r["lever"]:
            buckets["lever"].append(r["lever"])

        if r["workday"]:
            buckets["workday"].append(r["workday"])
        
        if r["workable"]:
            buckets["workable"].append(r["workable"])

        if r["jobvite"]:
            buckets["jobvite"].append(r["jobvite"])

    for ats in buckets:
        buckets[ats] = list(set(buckets[ats]))
    if to_detect:
        save_cache(cache)

    return buckets