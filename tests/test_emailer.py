from datetime import date

from emailer import build_email

ORDER = {
    "company_name": "Perry Properties Pty Ltd",
    "company_number": "002635421",
    "date_added": date(2026, 4, 20),
    "address": "43-51 Addison Road, Marrickville NSW 2204",
    "url": "https://www.nsw.gov.au/example-order",
    "earlier_orders": 0,
}


def test_email_has_the_company_details():
    message = build_email(ORDER, "monitor@example.com", ["someone@example.com"])
    body = message.get_content()

    assert message["Subject"] == "New stop work order: Perry Properties Pty Ltd"
    assert "Company name:    Perry Properties Pty Ltd" in body
    assert "Company number:  002 635 421" in body
    assert "Date added:      20 April 2026" in body
    assert "New company:     Yes" in body


def test_email_when_details_are_missing():
    order = {**ORDER, "company_number": None, "address": None, "earlier_orders": 2}
    body = build_email(order, "monitor@example.com", ["someone@example.com"]).get_content()

    assert "Company number:  Not published on the register" in body
    assert "Address:         Not listed" in body
    assert "New company:     No (2 earlier orders)" in body
