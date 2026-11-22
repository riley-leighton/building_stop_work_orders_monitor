import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

SITE = "https://www.nsw.gov.au"
# The register page is a React app that loads its results from this search API
SEARCH_URL = f"{SITE}/api/v1/elasticsearch/prod_content/_search"
SYDNEY = ZoneInfo("Australia/Sydney")
PAGE_SIZE = 20

COMPANY_IN_TITLE = re.compile(r"\border for (.+)$", re.IGNORECASE)
# e.g. "ACN 647 350 187", "A.C.N 601533519", "ACN 002635421"
ACN = re.compile(r"A\.?\s?C\.?\s?N\.?:?\s*(\d{3}\s?\d{3}\s?\d{3})")


def build_query(offset):
    return {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"type": "resource"}},
                    {"terms": {"agency_name": ["Building Commission NSW"]}},
                    {"terms": {"name_category": ["Stop work orders"]}},
                ],
            }
        },
        "sort": [{"resource_date": "desc"}, {"nid": "desc"}],
        "_source": ["nid", "title", "html_content", "summary", "url", "resource_date"],
        "from": offset,
        "size": PAGE_SIZE,
    }


def fetch_hits():
    hits = []
    while True:
        response = requests.post(SEARCH_URL, json=build_query(len(hits)), timeout=30)
        response.raise_for_status()
        page = response.json()["hits"]
        hits.extend(page["hits"])
        if not page["hits"] or len(hits) >= page["total"]["value"]:
            break

    if not hits:
        raise RuntimeError("No stop work orders returned, has the API changed?")
    return hits


def first(source, field):
    # Elasticsearch returns most fields as lists, e.g. "title": ["..."]
    value = source.get(field)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def to_sydney_date(timestamp):
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=SYDNEY).date()


def company_from_title(title):
    match = COMPANY_IN_TITLE.search(title)
    return match.group(1).strip() if match else title


def acn_from_html(html):
    text = BeautifulSoup(html or "", "html.parser").get_text(" ")
    match = ACN.search(text)
    return re.sub(r"\D", "", match.group(1)) if match else None


def parse_order(hit):
    source = hit["_source"]
    title = first(source, "title")
    return {
        "nid": first(source, "nid"),
        "title": title,
        "company_name": company_from_title(title),
        "company_number": acn_from_html(first(source, "html_content")),
        "address": first(source, "summary"),
        # Shown as the "Publication Date" on the order's page
        "date_added": to_sydney_date(first(source, "resource_date")),
        "url": SITE + first(source, "url"),
    }


def get_stop_work_orders():
    return [parse_order(hit) for hit in fetch_hits()]
