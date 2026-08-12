import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

def _format_size(size_bytes: int) -> str:
    """Format bytes into KB or MB."""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def get_dataset_overview(df: pd.DataFrame) -> Dict[str, Any]:
    memory_usage = df.memory_usage(deep=True).sum()
    return {
        "Total Rows": len(df),
        "Total Columns": len(df.columns),
        "Memory Usage": _format_size(memory_usage),
        "Total Missing Values": int(df.isna().sum().sum()),
        "Duplicate Rows": int(df.duplicated().sum()),
        "Unique Values": int(df.nunique().sum())
    }

def get_column_profile(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    profile_data = []
    for col in df.columns:
        profile_data.append({
            "Column Name": col,
            "Data Type": str(df[col].dtype),
            "Null Count": int(df[col].isna().sum()),
            "Unique Count": int(df[col].nunique())
        })
    profile_df = pd.DataFrame(profile_data)
    
    type_counts = {
        "Numeric Columns": len(df.select_dtypes(include=[np.number]).columns),
        "Categorical Columns": len(df.select_dtypes(include=['object', 'category']).columns),
        "Date Columns": len(df.select_dtypes(include=['datetime']).columns),
        "Boolean Columns": len(df.select_dtypes(include=['bool']).columns)
    }
    type_counts["Other Columns"] = len(df.columns) - sum(type_counts.values())
    
    return profile_df, type_counts

def get_missing_analysis(df: pd.DataFrame) -> pd.DataFrame:
    missing_count = df.isna().sum()
    missing_percent = (missing_count / len(df)) * 100
    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": missing_count.values,
        "Missing %": missing_percent.values
    }).sort_values(by="Missing Count", ascending=False).reset_index(drop=True)
    return missing_df

def get_duplicate_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    dup_sum = int(df.duplicated().sum())
    dup_percent = (dup_sum / len(df)) * 100 if len(df) > 0 else 0
    return {
        "Total Duplicate Rows": dup_sum,
        "Duplicate Percentage": f"{dup_percent:.2f}%"
    }

def get_statistical_summary(df: pd.DataFrame) -> pd.DataFrame:
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return pd.DataFrame()
    stats = num_df.describe().T
    
    # Calculate mode separately (taking the first mode if multiple exist)
    modes = num_df.mode()
    mode_series = modes.iloc[0] if not modes.empty else pd.Series(index=num_df.columns, dtype=float)
    
    stats['Mode'] = mode_series
    stats['Variance'] = num_df.var()
    stats = stats.rename(columns={
        "mean": "Mean", "50%": "Median", "min": "Min", "max": "Max", "std": "Std Dev"
    })
    return stats[['Mean', 'Median', 'Mode', 'Min', 'Max', 'Std Dev', 'Variance']]

def get_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return pd.DataFrame()
    return num_df.corr(numeric_only=True)

def get_categorical_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    cat_df = df.select_dtypes(include=['object', 'category'])
    results = {}
    for col in cat_df.columns:
        value_counts = cat_df[col].value_counts()
        if not value_counts.empty:
            results[col] = {
                "Unique Values": int(cat_df[col].nunique()),
                "Top Category": str(value_counts.index[0]),
                "Frequency": int(value_counts.iloc[0]),
                "Value Counts": value_counts
            }
    return results

def get_date_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    # Soft conversion to datetime for object columns that might be dates
    temp_df = df.copy()
    for col in temp_df.select_dtypes(include=['object']).columns:
        try:
            # We don't want to accidentally convert numerical strings, so only try if it looks like a date
            converted = pd.to_datetime(temp_df[col], errors='ignore')
            if pd.api.types.is_datetime64_any_dtype(converted):
                temp_df[col] = converted
        except Exception:
            pass

    date_cols = temp_df.select_dtypes(include=['datetime', 'datetimetz']).columns
    results = {}
    for col in date_cols:
        results[col] = {
            "Minimum Date": temp_df[col].min(),
            "Maximum Date": temp_df[col].max(),
            "Date Range": str(temp_df[col].max() - temp_df[col].min())
        }
    return results

def get_quality_indicators(df: pd.DataFrame) -> Dict[str, str]:
    if df.empty:
        return {}
        
    # Missing Values
    missing_pct = df.isna().sum().sum() / (df.shape[0] * df.shape[1])
    if missing_pct == 0:
        missing_status = "Good"
    elif missing_pct < 0.1:
        missing_status = "Warning"
    else:
        missing_status = "Critical"
        
    # Duplicates
    dup_pct = df.duplicated().sum() / len(df)
    if dup_pct == 0:
        dup_status = "Good"
    elif dup_pct < 0.05:
        dup_status = "Warning"
    else:
        dup_status = "Critical"
        
    # Data Type Consistency - Simplistic check for mixed types in object columns
    mixed_types = False
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].apply(type).nunique() > 1:
            mixed_types = True
            break
    type_status = "Warning" if mixed_types else "Good"
    
    # Memory Efficiency
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    if mem_mb < 50:
        mem_status = "Good"
    elif mem_mb < 100:
        mem_status = "Warning"
    else:
        mem_status = "Critical"
        
    return {
        "Missing Values": missing_status,
        "Duplicate Rows": dup_status,
        "Data Type Consistency": type_status,
        "Memory Efficiency": mem_status
    }
