# Building Stop Work Orders Monitor

Scrapes the stop work orders from the NSW [Register of Building Work Orders](https://www.nsw.gov.au/departments-and-agencies/building-commission/register-of-building-work-orders) using the search API behind the page, saves them to Postgres and sends an email when a new one is added.

## Setup

Needs Python 3.10+ and Postgres 14+.

```sh
createdb stop_work_orders
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in your database and SMTP details
python main.py
```

On Windows, activate the venv with `.venv\Scripts\activate`, and use Task Scheduler instead of cron.

For Gmail, turn on 2-Step Verification, create an app password at https://myaccount.google.com/apppasswords and use it as `SMTP_PASSWORD`.

The first run creates the tables and saves the orders already on the register without emailing. After that, each new order sends an email.

To see an email, delete an order and run it again:

```sh
psql stop_work_orders -c "DELETE FROM stop_work_orders WHERE nid = (SELECT max(nid) FROM stop_work_orders)"
python main.py
```

The email looks like this:

```
Subject: New stop work order: Sustainable Homes Australia R And D Pty Ltd

A new stop work order has been added to the NSW Register of Building Work Orders.

Company name: Sustainable Homes Australia R And D Pty Ltd
Company number: 647 350 187
Date added: 27 August 2026
Address: 14-17 Herd Street, Mount Hutton, NSW, 2290 (Lot 22/ DP1304602)
New company: No (2 earlier orders)

https://www.nsw.gov.au/departments-and-agencies/building-commission/register-of-building-work-orders/...
```

To keep it running, add a cron job, e.g. every hour:

```
0 * * * * cd /path/to/project && .venv/bin/python main.py >> monitor.log 2>&1
```

Tests: `python -m pytest`

## How it works

New orders are saved to the `stop_work_orders` table. A trigger on that table adds a row to `notifications` for each new order, and `main.py` emails any that haven't been sent yet. If an email fails, it's retried on the next run.

`exampledata/` has the request and responses I captured from the browser while working out the API. The tests use one of them.
