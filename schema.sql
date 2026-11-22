CREATE TABLE IF NOT EXISTS stop_work_orders (
    nid            integer PRIMARY KEY,
    title          text NOT NULL,
    company_name   text NOT NULL,
    company_number text,
    address        text,
    date_added     date,
    url            text,
    first_seen_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notifications (
    id         serial PRIMARY KEY,
    order_nid  integer NOT NULL REFERENCES stop_work_orders (nid) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    sent_at    timestamptz
);

-- Queue an email for every new order
CREATE OR REPLACE FUNCTION queue_notification() RETURNS trigger AS $$
BEGIN
    INSERT INTO notifications (order_nid) VALUES (NEW.nid);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER new_stop_work_order
    AFTER INSERT ON stop_work_orders
    FOR EACH ROW EXECUTE FUNCTION queue_notification();
