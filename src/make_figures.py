"""Render the three README figures (SVG) from the SQL views."""

import sys
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.rcParams["svg.hashsalt"] = "retail-cohort-lab"
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_sql import DB, build  # noqa: E402

OUT = Path("docs")
BLUE, GREY = "#2f5d8a", "#8a8f98"


def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)


def revenue_trend(con):
    df = con.sql("SELECT month, revenue / 1e6 AS revenue_m FROM monthly_kpis ORDER BY month").df()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar(df["month"].astype(str).str[:7], df["revenue_m"], color=BLUE)
    ax.set_title("Monthly revenue (GBP millions)", loc="left", fontweight="bold")
    ax.set_xticks(range(0, len(df), 3))
    ax.set_xticklabels(df["month"].astype(str).str[:7].iloc[::3], rotation=45, ha="right")
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "revenue_trend.svg")


def retention_heatmap(con):
    df = con.sql("""
        SELECT cohort_month, month_index, retention_pct
        FROM cohort_retention WHERE cohort_size >= 50 AND month_index <= 12
    """).df()
    grid = df.pivot(index="cohort_month", columns="month_index", values="retention_pct")
    fig, ax = plt.subplots(figsize=(8, 5.2))
    im = ax.imshow(grid.values, cmap="Blues", aspect="auto", vmin=0, vmax=60)
    ax.set_yticks(range(len(grid)))
    ax.set_yticklabels(grid.index.astype(str).str[:7])
    ax.set_xticks(range(grid.shape[1]))
    ax.set_xlabel("Months since first purchase")
    ax.set_title("Cohort retention (% of cohort still buying)", loc="left", fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(OUT / "cohort_retention.svg")


def segment_share(con):
    df = con.sql("SELECT segment, pct_customers, pct_revenue FROM segment_summary ORDER BY pct_revenue").df()
    fig, ax = plt.subplots(figsize=(8, 3.8))
    y = range(len(df))
    ax.barh([i + 0.2 for i in y], df["pct_customers"], height=0.4, color=GREY, label="% of customers")
    ax.barh([i - 0.2 for i in y], df["pct_revenue"], height=0.4, color=BLUE, label="% of revenue")
    ax.set_yticks(list(y))
    ax.set_yticklabels(df["segment"])
    ax.set_title("RFM segments: customers vs revenue", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "segments.svg")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB))
    build(con)
    revenue_trend(con)
    retention_heatmap(con)
    segment_share(con)
    print("wrote docs/revenue_trend.svg, docs/cohort_retention.svg, docs/segments.svg")


if __name__ == "__main__":
    main()
