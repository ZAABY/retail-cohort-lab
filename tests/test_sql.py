"""Tests run the real SQL files against a tiny hand-built dataset with known answers."""

from pathlib import Path

import duckdb
import pandas as pd
import pytest

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


@pytest.fixture()
def con():
    rows = [
        # invoice, stock, desc, qty, ts, price, customer, country
        ("1", "A", "widget", 2, "2024-01-05 10:00", 5.0, 1, "UK"),
        ("2", "A", "widget", 1, "2024-02-10 10:00", 5.0, 1, "UK"),
        ("3", "G", "gadget", 4, "2024-01-20 11:00", 2.5, 2, "UK"),
        ("4", "G", "gadget", 1, "2024-02-02 11:00", 2.5, 3, "DE"),
        ("C5", "A", "widget", -1, "2024-02-11 10:00", 5.0, 1, "UK"),   # return
        ("6", "POST", "postage", 1, "2024-01-06 10:00", 10.0, 1, "UK"),  # fee
        ("7", "A", "widget", 3, "2024-03-01 09:00", 0.0, 2, "UK"),     # free item
        ("8", "A", "widget", 1, "2024-03-02 09:00", 5.0, None, "UK"),  # guest checkout
    ]
    df = pd.DataFrame(rows, columns=["invoice", "stock_code", "description", "quantity", "invoice_ts", "unit_price", "customer_id", "country"])
    df["invoice_ts"] = pd.to_datetime(df["invoice_ts"])
    c = duckdb.connect()
    c.execute("CREATE TABLE raw_sales AS SELECT * FROM df")
    for path in sorted(SQL_DIR.glob("*.sql")):
        c.execute(path.read_text())
    return c


def test_cleaning_drops_returns_fees_and_free_rows(con):
    assert con.sql("SELECT count(*) FROM sales").fetchone()[0] == 5
    assert con.sql("SELECT count(*) FROM returns").fetchone()[0] == 1
    assert con.sql("SELECT sum(revenue) FROM sales").fetchone()[0] == pytest.approx(2 * 5 + 5 + 10 + 2.5 + 5)


def test_monthly_kpis(con):
    jan = con.sql("SELECT * FROM monthly_kpis WHERE month = DATE '2024-01-01'").df().iloc[0]
    assert jan["revenue"] == pytest.approx(10 + 10)
    assert jan["orders"] == 2
    assert jan["new_customers"] == 2 and jan["returning_customers"] == 0
    feb = con.sql("SELECT * FROM monthly_kpis WHERE month = DATE '2024-02-01'").df().iloc[0]
    assert feb["new_customers"] == 1 and feb["returning_customers"] == 1


def test_cohort_retention(con):
    r = con.sql("SELECT * FROM cohort_retention WHERE cohort_month = DATE '2024-01-01' ORDER BY month_index").df()
    assert r["cohort_size"].tolist() == [2, 2]
    assert r["retention_pct"].tolist() == [100.0, 50.0]


def test_cohort_ltv_is_cumulative(con):
    ltv = con.sql("SELECT * FROM cohort_ltv WHERE cohort_month = DATE '2024-01-01' ORDER BY month_index").df()
    assert ltv["cumulative_revenue_per_customer"].tolist() == [10.0, 12.5]


def test_rfm_covers_every_customer_once(con):
    assert con.sql("SELECT count(*) FROM rfm_segments").fetchone()[0] == 3
    assert con.sql("SELECT count(DISTINCT customer_id) FROM rfm_segments").fetchone()[0] == 3
    assert con.sql("SELECT sum(pct_customers) FROM segment_summary").fetchone()[0] == pytest.approx(100.0, abs=0.2)
