import pytest
import pandas as pd
from services.visualization_engine import (
    generate_auto_charts,
    create_custom_chart,
    create_ai_chart
)

def test_generate_auto_charts():
    df = pd.DataFrame({
        "revenue": [100.0, 200.0, 300.0],
        "cost": [50.0, 100.0, 150.0],
        "category": ["A", "B", "A"]
    })
    charts = generate_auto_charts(df)
    assert len(charts) >= 2
    types = [c["type"] for c in charts]
    assert "Histogram" in types
    assert "Bar" in types or "Pie" in types

def test_create_custom_chart_bar():
    df = pd.DataFrame({
        "dept": ["Engineering", "Sales", "Support"],
        "salary": [100000, 80000, 60000]
    })
    fig = create_custom_chart(df, "Bar", "dept", "salary", "SUM")
    assert fig is not None
    assert fig.data[0].type == "bar"

def test_create_custom_chart_pie():
    df = pd.DataFrame({
        "region": ["North", "South", "East"]
    })
    fig = create_custom_chart(df, "Pie", "region", None, "None")
    assert fig is not None
    assert fig.data[0].type == "pie"

def test_create_ai_chart():
    df = pd.DataFrame({
        "month": ["Jan", "Feb", "Mar"],
        "sales": [1500, 2200, 3100]
    })
    ch = create_ai_chart(df, "monthly sales trend")
    assert ch["fig"] is not None
    assert "Sales" in ch["title"]

