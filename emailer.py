import os
import smtplib
import ssl
from email.message import EmailMessage

BODY = """\
A new stop work order has been added to the NSW Register of Building Work Orders.

Company name:    {company_name}
Company number:  {company_number}
Date added:      {date_added}
Address:         {address}
New company:     {new_company}

{url}
"""


def format_acn(acn):
    if not acn:
        return "Not published on the register"
    return f"{acn[0:3]} {acn[3:6]} {acn[6:9]}"


def format_date(value):
    return f"{value.day} {value:%B %Y}" if value else "Unknown"


def format_new_company(earlier_orders):
    if earlier_orders == 0:
        return "Yes"
    return f"No ({earlier_orders} earlier order{'s' if earlier_orders > 1 else ''})"


def build_email(order, sender, recipients):
    message = EmailMessage()
    message["Subject"] = f"New stop work order: {order['company_name']}"
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(BODY.format(
        company_name=order["company_name"],
        company_number=format_acn(order["company_number"]),
        date_added=format_date(order["date_added"]),
        address=order["address"] or "Not listed",
        new_company=format_new_company(order["earlier_orders"]),
        url=order["url"],
    ))
    return message


def connect():
    smtp = smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=30)
    if os.environ.get("SMTP_USER"):
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
    return smtp
