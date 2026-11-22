import json
from datetime import date, datetime, timezone
from pathlib import Path

from scraper import acn_from_html, company_from_title, parse_order, to_sydney_date

EXAMPLE_RESPONSE = Path(__file__).parent.parent / "exampledata" / "stop_work_orders_response.json"


def example_hits():
    return json.loads(EXAMPLE_RESPONSE.read_text())["hits"]["hits"]


def test_company_from_title():
    assert company_from_title("Stop Work Order for Perry Properties Pty Ltd") == "Perry Properties Pty Ltd"
    assert company_from_title("Stop Work order for Richmond Rose Bay Pty Ltd") == "Richmond Rose Bay Pty Ltd"
    assert company_from_title("Modified Stop Work Order for Natoby Pty Ltd") == "Natoby Pty Ltd"
    assert company_from_title(
        "Notice of Imposition of a Condition Upon a Stop Work Order for Sustainable Homes Australia R And D Pty Ltd"
    ) == "Sustainable Homes Australia R And D Pty Ltd"


def test_company_from_title_falls_back_to_whole_title():
    assert company_from_title("Something unexpected") == "Something unexpected"


def test_acn_formats():
    assert acn_from_html("<p>Sustainable Homes (ACN 647 350 187) (the Subject)</p>") == "647350187"
    assert acn_from_html("<li>Natoby Pty Ltd (A.C.N 601533519) (the Developer)</li>") == "601533519"
    assert acn_from_html("<li>Perry Properties Pty Ltd (ACN 002635421) (the Developer)</li>") == "002635421"


def test_acn_is_not_confused_with_abn():
    html = "<p>Richmond Rose Bay Pty Ltd (ACN 636 583 581) as trustee for The Richmond Rose Bay Unit Trust (ABN 27 184 210 983)</p>"
    assert acn_from_html(html) == "636583581"


def test_no_acn():
    assert acn_from_html("<p>Ausfield Investment Pty Ltd (the Developer) is issued with this Stop Work Order</p>") is None
    assert acn_from_html(None) is None


def test_dates_use_sydney_time():
    # 10:30pm UTC on 6 July is 8:30am on 7 July in Sydney
    timestamp = datetime(2026, 7, 6, 22, 30, tzinfo=timezone.utc).timestamp()
    assert to_sydney_date(timestamp) == date(2026, 7, 7)


def test_parse_order():
    hit = next(hit for hit in example_hits() if hit["_source"]["nid"] == [117218])
    assert parse_order(hit) == {
        "nid": 117218,
        "title": "Stop Work Order for Perry Properties Pty Ltd",
        "company_name": "Perry Properties Pty Ltd",
        "company_number": "002635421",
        "address": "43-51 Addison Road, Marrickville NSW 2204 Lot 101/ DP 1304727",
        "date_added": date(2026, 4, 20),
        "url": "https://www.nsw.gov.au/departments-and-agencies/building-commission/register-of-building-work-orders/stop-work-order-for-perry-properties-pty-ltd",
    }


def test_every_example_order_has_a_company_name():
    for hit in example_hits():
        order = parse_order(hit)
        assert order["company_name"] != order["title"]
