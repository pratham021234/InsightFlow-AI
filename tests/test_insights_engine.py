import pytest
import pandas as pd
from services.insights_engine import (
    generate_executive_summary,
    generate_key_findings,
    analyze_trends,
    detect_anomalies,
    identify_risks,
    format_export_text
)

def test_executive_summary():
    df = pd.DataFrame({"sales": [100, 200], "region": ["North", "South"]})
    kpis = [{"name": "Total Sales", "value": "300.00"}]
    summary = generate_executive_summary(df, "Sales", kpis)
    assert "2 records" in summary
    assert "Total Sales at 300.00" in summary

def test_key_findings():
    df = pd.DataFrame({
        "variance_col": [1.0, 50.0, 200.0, 2.0],
        "corr_a": [1, 2, 3, 4],
        "corr_b": [10, 20, 30, 40],
        "category": ["A", "A", "A", "B"]
    })
    findings = generate_key_findings(df, "Sales")
    assert len(findings) >= 2
    assert any("Correlation" in f["title"] for f in findings)
    assert any("Dominant Segment" in f["title"] for f in findings)

def test_format_export_text():
    text = format_export_text(
        "Executive Summary test",
        [{"title": "Finding 1", "description": "Desc 1", "priority": "High"}],
        [], [], [], [], [], []
    )
    assert "INSIGHTFLOW AI" in text
    assert "Finding 1" in text

