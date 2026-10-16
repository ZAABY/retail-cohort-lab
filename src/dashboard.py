"""Streamlit dashboard over the SQL views.  Run: streamlit run src/dashboard.py"""

import sys
from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_sql import DB, build  # noqa: E402

st.set_page_config(page_title="Retail cohort lab", layout="wide")


@st.cache_resource
def connect():
    con = duckdb.connect(str(DB), read_only=False)
    build(con)
    return con


con = connect()
st.title("Retail cohort lab")
st.caption("UCI Online Retail II, Dec 2009 - Dec 2011. All numbers come from the SQL in /sql.")

kpis = con.sql("SELECT * FROM monthly_kpis ORDER BY month").df()
c1, c2, c3 = st.columns(3)
c1.metric("Revenue (GBP)", f"{kpis['revenue'].sum():,.0f}")
c2.metric("Orders", f"{int(kpis['orders'].sum()):,}")
c3.metric("Identified customers", f"{con.sql('SELECT count(*) FROM first_purchase').fetchone()[0]:,}")

tab1, tab2, tab3 = st.tabs(["Revenue", "Cohorts", "RFM segments"])

with tab1:
    st.plotly_chart(px.bar(kpis, x="month", y="revenue", title="Monthly revenue"))
    both = kpis.melt(id_vars="month", value_vars=["new_customers", "returning_customers"])
    st.plotly_chart(px.bar(both, x="month", y="value", color="variable", title="New vs returning customers"),
                    width="stretch")

with tab2:
    min_size = st.slider("Minimum cohort size", 0, 500, 50)
    ret = con.sql(f"""
        SELECT cohort_month, month_index, retention_pct
        FROM cohort_retention WHERE cohort_size >= {int(min_size)} AND month_index <= 12
    """).df()
    grid = ret.pivot(index="cohort_month", columns="month_index", values="retention_pct")
    st.plotly_chart(px.imshow(grid, aspect="auto", color_continuous_scale="Blues",
                              labels=dict(color="% retained")))
    ltv = con.sql("SELECT * FROM cohort_ltv WHERE month_index <= 12").df()
    st.plotly_chart(px.line(ltv, x="month_index", y="cumulative_revenue_per_customer",
                            color=ltv["cohort_month"].astype(str), title="Cumulative revenue per customer"),
                    width="stretch")

with tab3:
    seg = con.sql("SELECT * FROM segment_summary").df()
    st.dataframe(seg, hide_index=True)
    st.plotly_chart(px.bar(seg, x="segment", y=["pct_customers", "pct_revenue"], barmode="group"),
                    width="stretch")
