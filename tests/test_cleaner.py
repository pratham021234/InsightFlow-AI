import pytest
import pandas as pd
import numpy as np
from services.cleaner import (
    detect_missing_values, fill_missing_values,
    detect_duplicates, remove_duplicates,
    detect_outliers, cap_outliers, remove_outliers,
    convert_dtype, rename_columns, drop_columns
)

def test_missing_values_detection_and_imputation():
    df = pd.DataFrame({
        "num": [10.0, np.nan, 30.0],
        "cat": ["A", np.nan, "A"]
    })
    issues = detect_missing_values(df)
    assert len(issues) == 2
    
    # Fill Median
    cleaned_num = fill_missing_values(df, "num", "Fill Median")
    assert cleaned_num["num"].isna().sum() == 0
    assert cleaned_num.loc[1, "num"] == 20.0
    
    # Fill Mode on text
    cleaned_cat = fill_missing_values(df, "cat", "Fill Mode")
    assert cleaned_cat["cat"].isna().sum() == 0
    assert cleaned_cat.loc[1, "cat"] == "A"
    
    # Drop rows
    dropped = fill_missing_values(df, "num", "Remove Rows")
    assert len(dropped) == 2

def test_duplicate_removal():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [10, 10, 20]})
    assert detect_duplicates(df) == 1
    cleaned = remove_duplicates(df)
    assert len(cleaned) == 2
    assert detect_duplicates(cleaned) == 0

def test_outlier_detection_and_capping():
    # 10 values with one extreme outlier
    data = [10.0, 11.0, 12.0, 10.5, 11.2, 10.8, 12.1, 11.5, 10.9, 1000.0]
    df = pd.DataFrame({"val": data})
    outliers = detect_outliers(df)
    assert len(outliers) == 1
    assert outliers[0]["Outlier Count"] == 1
    
    capped = cap_outliers(df, "val", outliers[0]["Lower Bound"], outliers[0]["Upper Bound"])
    assert capped["val"].max() <= outliers[0]["Upper Bound"]

def test_column_operations():
    df = pd.DataFrame({"old_name": [1, 2], "to_drop": [3, 4]})
    renamed = rename_columns(df, {"old_name": "new_name"})
    assert "new_name" in renamed.columns
    
    dropped = drop_columns(renamed, ["to_drop"])
    assert "to_drop" not in dropped.columns
    assert len(dropped.columns) == 1

