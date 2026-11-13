import pytest
import pandas as pd
import numpy as np
from services.profiler import (
    get_dataset_overview,
    get_column_profile,
    get_missing_analysis,
    get_duplicate_analysis,
    get_statistical_summary,
    get_correlation_matrix,
    get_quality_indicators
)

def test_profiler_overview():
    df = pd.DataFrame({
        "num": [10, 20, 30, np.nan],
        "cat": ["A", "B", "A", "C"]
    })
    overview = get_dataset_overview(df)
    assert overview["Total Rows"] == 4
    assert overview["Total Columns"] == 2
    assert overview["Total Missing Values"] == 1
    assert overview["Duplicate Rows"] == 0

def test_profiler_column_profile():
    df = pd.DataFrame({
        "age": [25, 30, 35],
        "city": ["NY", "SF", "LA"]
    })
    prof_df, type_counts = get_column_profile(df)
    assert len(prof_df) == 2
    assert type_counts["Numeric Columns"] == 1
    assert type_counts["Categorical Columns"] == 1

def test_statistical_summary():
    df = pd.DataFrame({
        "values": [10.0, 20.0, 30.0, 40.0, 50.0]
    })
    stats = get_statistical_summary(df)
    assert "Mean" in stats.columns
    assert stats.loc["values", "Mean"] == 30.0
    assert stats.loc["values", "Median"] == 30.0

def test_correlation_matrix():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [2, 4, 6, 8, 10]
    })
    corr = get_correlation_matrix(df)
    assert round(corr.loc["x", "y"], 1) == 1.0

def test_quality_indicators():
    df = pd.DataFrame({
        "a": [1, 2, 3],
        "b": ["x", "y", "z"]
    })
    qual = get_quality_indicators(df)
    assert qual["Missing Values"] == "Good"
    assert qual["Duplicate Rows"] == "Good"

