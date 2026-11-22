import os
import smtplib

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

import db
import emailer
from scraper import get_stop_work_orders


def send_notifications(conn):
    pending = db.pending_notifications(conn)
    if not pending:
        return

    sender = os.environ["MAIL_FROM"]
    recipients = [address.strip() for address in os.environ["NOTIFY_TO"].split(",")]
    with emailer.connect() as smtp:
        for order in pending:
            try:
                smtp.send_message(emailer.build_email(order, sender, recipients))
            except smtplib.SMTPException as error:
                print(f"Couldn't send email for {order['company_name']}: {error}")
                continue
            db.mark_sent(conn, order["notification_id"])
            conn.commit()
            print(f"Emailed: {order['company_name']}")


def main():
    load_dotenv()
    orders = get_stop_work_orders()
    print(f"Found {len(orders)} stop work orders on the register")

    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row) as conn:
        db.create_tables(conn)
        first_run = db.is_empty(conn)
        new_count = db.save_orders(conn, orders)
        if first_run:
            # Don't email about everything that's already on the register
            db.clear_notifications(conn)
            print(f"First run: saved {new_count} existing orders, no emails sent")
        else:
            print(f"{new_count} new")
        conn.commit()

        send_notifications(conn)


if __name__ == "__main__":
    main()
