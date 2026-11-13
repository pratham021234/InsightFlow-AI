import pytest
import pandas as pd
from services.kpi_engine import (
    generate_default_kpis,
    create_manual_kpi,
    create_ai_kpi,
    calculate_aggregation
)

def test_default_sales_kpis():
    df = pd.DataFrame({
        "order_id": [1, 2, 3],
        "customer": ["C1", "C2", "C1"],
        "revenue": [100.0, 200.0, 300.0],
        "product": ["P1", "P2", "P1"]
    })
    kpis = generate_default_kpis(df, "Sales")
    assert any(k["name"] == "Total Revenue" for k in kpis)
    rev_kpi = next(k for k in kpis if k["name"] == "Total Revenue")
    assert rev_kpi["value"] == "600.00"

def test_manual_kpi_builder():
    df = pd.DataFrame({"score": [10, 20, 30, 40]})
    kpi = create_manual_kpi(df, "Average Score", "score", "AVG")
    assert kpi["name"] == "Average Score"
    assert kpi["value"] == "25.00"

def test_ai_kpi_builder_profit_margin():
    df = pd.DataFrame({
        "revenue": [1000.0, 2000.0],
        "cost": [600.0, 1000.0]
    })
    # Total revenue = 3000, Total cost = 1600. Profit = 1400. Margin = 1400/3000 = 46.67%
    kpi = create_ai_kpi(df, "Calculate profit margin")
    assert "Margin" in kpi["name"]
    assert "46.67%" in kpi["value"]

def test_ai_kpi_builder_average():
    df = pd.DataFrame({"units": [10, 20, 30]})
    kpi = create_ai_kpi(df, "average units")
    assert "units" in kpi["name"].lower()
    assert kpi["value"] == "20.00"

