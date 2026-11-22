from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")

INSERT_ORDER = """
    INSERT INTO stop_work_orders
        (nid, title, company_name, company_number, address, date_added, url)
    VALUES (
        %(nid)s, %(title)s, %(company_name)s,
        -- not every order mentions the ACN, so reuse one from another order for the same company
        COALESCE(%(company_number)s, (
            SELECT company_number FROM stop_work_orders
            WHERE lower(company_name) = lower(%(company_name)s) AND company_number IS NOT NULL
            LIMIT 1
        )),
        %(address)s, %(date_added)s, %(url)s
    )
    ON CONFLICT (nid) DO NOTHING
    RETURNING nid
"""


def create_tables(conn):
    conn.execute(SCHEMA.read_text())


def is_empty(conn):
    return conn.execute("SELECT count(*) AS total FROM stop_work_orders").fetchone()["total"] == 0


def save_orders(conn, orders):
    new_count = 0
    # Oldest first so newer orders can pick up an ACN from older ones
    for order in sorted(orders, key=lambda order: order["nid"]):
        if conn.execute(INSERT_ORDER, order).fetchone():
            new_count += 1
    return new_count


def clear_notifications(conn):
    conn.execute("DELETE FROM notifications WHERE sent_at IS NULL")


def pending_notifications(conn):
    return conn.execute("""
        SELECT n.id AS notification_id, o.*, (
            SELECT count(*) FROM stop_work_orders earlier
            WHERE lower(earlier.company_name) = lower(o.company_name) AND earlier.nid < o.nid
        ) AS earlier_orders
        FROM notifications n
        JOIN stop_work_orders o ON o.nid = n.order_nid
        WHERE n.sent_at IS NULL
        ORDER BY n.id
    """).fetchall()


def mark_sent(conn, notification_id):
    conn.execute("UPDATE notifications SET sent_at = now() WHERE id = %s", [notification_id])
