import pytest
import pandas as pd
from services.dataset_detector import (
    detect_dataset_type,
    generate_dataset_description,
    extract_business_entities,
    generate_kpi_suggestions,
    generate_chart_suggestions
)

def test_detect_sales_domain():
    df = pd.DataFrame({
        "order_id": [1, 2],
        "customer_name": ["Alice", "Bob"],
        "product_name": ["Pro Plan", "Starter"],
        "revenue": [500.0, 150.0],
        "discount": [10.0, 0.0]
    })
    domain, conf, scores = detect_dataset_type(df)
    assert domain == "Sales"
    assert conf > 50

def test_detect_hr_domain():
    df = pd.DataFrame({
        "employee_id": [101, 102],
        "department": ["Eng", "Sales"],
        "salary": [95000, 75000],
        "attrition": ["No", "Yes"]
    })
    domain, conf, scores = detect_dataset_type(df)
    assert domain == "HR"
    assert conf > 50

def test_detect_general_domain():
    df = pd.DataFrame({
        "col_x": [1, 2, 3],
        "col_y": ["a", "b", "c"]
    })
    domain, conf, scores = detect_dataset_type(df)
    assert domain == "General Dataset"

def test_extract_entities():
    df = pd.DataFrame({
        "customer_id": [1, 2],
        "product": ["A", "B"],
        "revenue": [100, 200]
    })
    entities = extract_business_entities(df, "Sales")
    assert len(entities) >= 2
    assert "customer_id" in entities or "product" in entities or "revenue" in entities

def test_kpi_and_chart_suggestions():
    kpis = generate_kpi_suggestions("Sales")
    charts = generate_chart_suggestions("Sales")
    assert any("Revenue" in k for k in kpis)
    assert len(charts) >= 3

