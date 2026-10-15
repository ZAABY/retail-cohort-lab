"""Run the SQL layer against data/retail.duckdb and print the headline numbers."""

import sys
from pathlib import Path

import duckdb

DB = Path("data/retail.duckdb")
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def build(con: duckdb.DuckDBPyConnection) -> None:
    """Create every view, in file order (01 clean, 02 kpis, 03 cohorts, 04 rfm)."""
    for path in sorted(SQL_DIR.glob("*.sql")):
        con.execute(path.read_text())


def main() -> None:
    if not DB.exists():
        sys.exit(f"{DB} not found. Run `python src/load.py` first.")
    con = duckdb.connect(str(DB))
    build(con)
    print("Segment summary")
    print(con.sql("SELECT * FROM segment_summary").df().to_string(index=False))
    print("\nMonth-1 retention (all cohorts, weighted)")
    print(con.sql("""
        SELECT round(100.0 * sum(active_customers) / sum(cohort_size), 1) AS month1_retention_pct
        FROM cohort_retention WHERE month_index = 1
    """).df().to_string(index=False))


if __name__ == "__main__":
    main()
