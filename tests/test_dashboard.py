"""Run the dashboard against a disposable database, never the user's data."""
from pathlib import Path
from test_sql import con  # noqa: F401

import pytest

pytest.importorskip("streamlit", reason="Install requirements.txt to run dashboard tests")
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


def test_dashboard_renders_all_tabs(con, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data').mkdir()
    rows = con.sql('SELECT * FROM raw_sales').df()
    import duckdb
    with duckdb.connect(str(tmp_path / 'data' / 'retail.duckdb')) as db:
        db.execute('CREATE TABLE raw_sales AS SELECT * FROM rows')
    app = AppTest.from_file(str(ROOT / 'src' / 'dashboard.py')).run(timeout=30)
    assert not app.exception
    assert [metric.label for metric in app.metric] == [
        'Revenue (GBP)', 'Orders', 'Identified customers'
    ]
    assert app.metric[2].value == '3'
    assert [tab.label for tab in app.tabs] == ['Revenue', 'Cohorts', 'RFM segments']
    assert len(app.get('plotly_chart')) == 5
    assert len(app.dataframe) == 1
    app.slider[0].set_value(0).run(timeout=30)
    assert not app.exception
