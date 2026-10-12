"""Load the UCI Online Retail II workbook into a DuckDB file (data/retail.duckdb)."""

import sys
from pathlib import Path

import duckdb
import pandas as pd

RAW = Path("data/online_retail_II.xlsx")
DB = Path("data/retail.duckdb")


def main() -> None:
    sheets = pd.read_excel(RAW, sheet_name=None, engine="openpyxl")
    df = pd.concat(sheets.values(), ignore_index=True)
    df.columns = ["invoice", "stock_code", "description", "quantity", "invoice_ts",
                  "unit_price", "customer_id", "country"]
    df["invoice"] = df["invoice"].astype(str)
    df["stock_code"] = df["stock_code"].astype(str)
    con = duckdb.connect(str(DB))
    con.execute("CREATE OR REPLACE TABLE raw_sales AS SELECT * FROM df")
    n = con.execute("SELECT count(*) FROM raw_sales").fetchone()[0]
    print(f"loaded {n:,} rows into {DB}", file=sys.stderr)


if __name__ == "__main__":
    main()
