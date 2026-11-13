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
    total_cells = df.shape[0] * df.shape[1] if df.shape[0] * df.shape[1] > 0 else 1
    total_missing = int(df.isna().sum().sum())
    return {
        "Total Rows": len(df),
        "Total Columns": len(df.columns),
        "Memory Usage": _format_size(memory_usage),
        "Total Missing Values": total_missing,
        "Missing Ratio": f"{(total_missing / total_cells) * 100:.2f}%",
        "Duplicate Rows": int(df.duplicated().sum()),
        "Duplicate Ratio": f"{(df.duplicated().sum() / len(df) * 100):.2f}%" if len(df) > 0 else "0.00%",
        "Unique Values": int(df.nunique().sum())
    }

def get_column_profile(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    profile_data = []
    total_rows = len(df) if len(df) > 0 else 1
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        profile_data.append({
            "Column Name": col,
            "Data Type": str(df[col].dtype),
            "Null Count": null_count,
            "Null %": f"{(null_count / total_rows) * 100:.1f}%",
            "Unique Count": int(df[col].nunique())
        })
    profile_df = pd.DataFrame(profile_data)
    
    type_counts = {
        "Numeric Columns": len(df.select_dtypes(include=[np.number]).columns),
        "Categorical Columns": len(df.select_dtypes(include=['object', 'category']).columns),
        "Date Columns": len(df.select_dtypes(include=['datetime', 'datetimetz']).columns),
        "Boolean Columns": len(df.select_dtypes(include=['bool']).columns)
    }
    type_counts["Other Columns"] = len(df.columns) - sum(type_counts.values())
    
    return profile_df, type_counts

def get_missing_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=["Column", "Missing Count", "Missing %"])
    missing_count = df.isna().sum()
    missing_percent = (missing_count / len(df)) * 100
    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": missing_count.values,
        "Missing %": np.round(missing_percent.values, 2)
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
    if num_df.empty or len(num_df) == 0:
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
    cols_order = [c for c in ['Mean', 'Median', 'Mode', 'Min', 'Max', 'Std Dev', 'Variance'] if c in stats.columns]
    return stats[cols_order].round(3)

def get_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty or num_df.shape[1] < 2:
        return pd.DataFrame()
    return num_df.corr(numeric_only=True).round(3)

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
    temp_df = df.copy()
    results = {}
    
    # First check existing datetime columns
    date_cols = temp_df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
    
    # Also inspect object columns that might represent dates
    for col in temp_df.select_dtypes(include=['object']).columns:
        try:
            converted = pd.to_datetime(temp_df[col], errors='coerce')
            if converted.notna().sum() > len(temp_df) * 0.7:  # At least 70% valid dates
                temp_df[col] = converted
                date_cols.append(col)
        except Exception:
            pass

    for col in set(date_cols):
        series = temp_df[col].dropna()
        if not series.empty:
            min_date = series.min()
            max_date = series.max()
            results[col] = {
                "Minimum Date": str(min_date)[:19],
                "Maximum Date": str(max_date)[:19],
                "Date Range": str(max_date - min_date)
            }
    return results

def get_quality_indicators(df: pd.DataFrame) -> Dict[str, str]:
    if df.empty or len(df) == 0:
        return {}
        
    # Missing Values Indicator
    total_cells = df.shape[0] * df.shape[1]
    missing_pct = df.isna().sum().sum() / total_cells if total_cells > 0 else 0
    if missing_pct == 0:
        missing_status = "Good"
    elif missing_pct < 0.08:
        missing_status = "Warning"
    else:
        missing_status = "Critical"
        
    # Duplicates Indicator
    dup_pct = df.duplicated().sum() / len(df) if len(df) > 0 else 0
    if dup_pct == 0:
        dup_status = "Good"
    elif dup_pct < 0.05:
        dup_status = "Warning"
    else:
        dup_status = "Critical"
        
    # Data Type Consistency Indicator
    mixed_types = False
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].apply(type).nunique() > 1:
            mixed_types = True
            break
    type_status = "Warning" if mixed_types else "Good"
    
    # Memory Efficiency Indicator
    mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    if mem_mb < 50:
        mem_status = "Good"
    elif mem_mb < 150:
        mem_status = "Warning"
    else:
        mem_status = "Critical"
        
    return {
        "Missing Values": missing_status,
        "Duplicate Rows": dup_status,
        "Data Type Consistency": type_status,
        "Memory Efficiency": mem_status
    }
