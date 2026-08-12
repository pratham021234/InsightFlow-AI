import pandas as pd
import numpy as np
from typing import List, Dict, Any

def detect_missing_values(df: pd.DataFrame) -> List[Dict[str, Any]]:
    missing = df.isna().sum()
    missing_pct = (missing / len(df)) * 100
    missing_cols = missing[missing > 0].index.tolist()
    
    results = []
    for col in missing_cols:
        dtype = str(df[col].dtype)
        if 'datetime' in dtype:
            suggestion = "Forward Fill"
        elif df[col].dtype.kind in 'bifc':
            suggestion = "Fill Median"
        else:
            suggestion = "Fill Mode"
        results.append({
            "Column Name": col,
            "Missing Count": int(missing[col]),
            "Missing Percentage": f"{missing_pct[col]:.2f}%",
            "Suggested Fix": suggestion,
            "Data Type": dtype
        })
    return results

def fill_missing_values(df: pd.DataFrame, column: str, strategy: str) -> pd.DataFrame:
    df_clean = df.copy()
    if strategy == "Fill Mean":
        val = df_clean[column].mean()
        df_clean[column] = df_clean[column].fillna(val)
    elif strategy == "Fill Median":
        val = df_clean[column].median()
        df_clean[column] = df_clean[column].fillna(val)
    elif strategy == "Fill Mode":
        mode_series = df_clean[column].mode()
        if not mode_series.empty:
            df_clean[column] = df_clean[column].fillna(mode_series.iloc[0])
    elif strategy == "Forward Fill":
        df_clean[column] = df_clean[column].ffill()
    elif strategy == "Backward Fill":
        df_clean[column] = df_clean[column].bfill()
    elif strategy == "Remove Rows":
        df_clean = df_clean.dropna(subset=[column])
    return df_clean

def detect_duplicates(df: pd.DataFrame) -> int:
    return int(df.duplicated().sum())

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates()

def detect_outliers(df: pd.DataFrame) -> List[Dict[str, Any]]:
    results = []
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        
        outliers = df[(df[col] < lower) | (df[col] > upper)]
        if not outliers.empty:
            results.append({
                "Column Name": col,
                "Outlier Count": len(outliers),
                "Outlier Percentage": f"{(len(outliers) / len(df)) * 100:.2f}%",
                "Lower Bound": float(lower),
                "Upper Bound": float(upper)
            })
    return results

def remove_outliers(df: pd.DataFrame, column: str, lower: float, upper: float) -> pd.DataFrame:
    # Filter rows ignoring NAs to avoid dropping missing values by accident during outlier removal
    mask = (df[column].isna()) | ((df[column] >= lower) & (df[column] <= upper))
    return df[mask]

def cap_outliers(df: pd.DataFrame, column: str, lower: float, upper: float) -> pd.DataFrame:
    df_clean = df.copy()
    df_clean[column] = np.where(df_clean[column] < lower, lower, df_clean[column])
    df_clean[column] = np.where(df_clean[column] > upper, upper, df_clean[column])
    return df_clean

def detect_dtype_issues(df: pd.DataFrame) -> List[Dict[str, str]]:
    results = []
    for col in df.select_dtypes(include=['object']).columns:
        # Check if it could be numeric
        try:
            converted = pd.to_numeric(df[col].dropna())
            if not converted.empty:
                results.append({"Column Name": col, "Issue": "Numeric stored as object", "Suggestion": "Convert to Numeric"})
                continue
        except Exception:
            pass
        
        # Check if it could be datetime
        try:
            # simple check on first non-null
            first_val = df[col].dropna().iloc[0]
            pd.to_datetime(str(first_val))
            results.append({"Column Name": col, "Issue": "Date stored as string", "Suggestion": "Convert to Datetime"})
            continue
        except Exception:
            pass
            
        # Check cardinality for category conversion
        if df[col].nunique() < 20 and len(df) > 100:
            results.append({"Column Name": col, "Issue": "Low cardinality string", "Suggestion": "Convert to Category"})
            
    return results

def convert_dtype(df: pd.DataFrame, column: str, target_type: str) -> pd.DataFrame:
    df_clean = df.copy()
    if target_type == "Convert to Numeric":
        df_clean[column] = pd.to_numeric(df_clean[column], errors='coerce')
    elif target_type == "Convert to Datetime":
        df_clean[column] = pd.to_datetime(df_clean[column], errors='coerce')
    elif target_type == "Convert to Category":
        df_clean[column] = df_clean[column].astype('category')
    return df_clean

def rename_columns(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    return df.rename(columns=mapping)

def drop_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    return df.drop(columns=columns, errors='ignore')

def generate_cleaning_summary(log: List[Dict[str, str]]) -> pd.DataFrame:
    if not log:
        return pd.DataFrame(columns=["Operation", "Affected Rows", "Affected Columns", "Timestamp"])
    return pd.DataFrame(log)
