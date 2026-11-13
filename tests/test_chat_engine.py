import pytest
import pandas as pd
from services.chat_engine import (
    detect_intent,
    extract_entities,
    handle_metadata_questions,
    execute_query
)

def test_detect_intent():
    assert detect_intent("how many rows exist") == "Metadata"
    assert detect_intent("who are the top 5 customers") == "Ranking"
    assert detect_intent("monthly revenue trend over time") == "Trend"
    assert detect_intent("compare sales vs region") == "Comparison"

def test_extract_entities():
    df = pd.DataFrame({
        "revenue": [100, 200],
        "region": ["North", "South"]
    })
    measure, dimension = extract_entities("show sales across regions", df)
    assert measure == "revenue"
    assert dimension == "region"

def test_execute_query_ranking():
    df = pd.DataFrame({
        "customer": ["Alice", "Bob", "Charlie"],
        "sales": [500.0, 1200.0, 300.0]
    })
    result = execute_query(df, "Ranking", "sales", "customer", raw_query="top customer by sales")
    assert "Bob" in result["text"]
    assert "1,200.00" in result["text"]
    assert result["fig"] is not None

def test_execute_query_aggregation():
    df = pd.DataFrame({
        "revenue": [100.0, 200.0, 300.0]
    })
    result = execute_query(df, "Aggregation", "revenue", None, raw_query="what is total revenue")
    assert "600.00" in result["text"]

