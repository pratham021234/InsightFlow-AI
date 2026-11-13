import pandas as pd
import numpy as np
import uuid
import json
from typing import Dict, List, Any, Optional
from services.ai_service import query_gemini

def _format_value(val: Any) -> str:
    try:
        if isinstance(val, (int, np.integer)):
            return f"{val:,}"
        elif isinstance(val, (float, np.floating)):
            if pd.isna(val):
                return "N/A"
            if abs(val) >= 1_000_000:
                return f"{val / 1_000_000:.2f}M"
            elif abs(val) >= 1_000:
                return f"{val / 1_000:.2f}K"
            else:
                return f"{val:.2f}"
        return str(val)
    except Exception:
        return str(val)

def detect_relevant_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
    """Find the best column matching a list of keywords."""
    for col in df.columns:
        if any(kw.lower() in str(col).lower() for kw in keywords):
            return col
    return None

def calculate_aggregation(df: pd.DataFrame, column: str, agg_type: str) -> Any:
    if column not in df.columns:
        return None
        
    series = df[column].dropna()
    if series.empty:
        return None
        
    try:
        if agg_type == "SUM":
            return series.sum() if pd.api.types.is_numeric_dtype(series) else None
        elif agg_type == "AVG":
            return series.mean() if pd.api.types.is_numeric_dtype(series) else None
        elif agg_type == "COUNT":
            return series.count()
        elif agg_type == "COUNT DISTINCT":
            return series.nunique()
        elif agg_type == "MIN":
            return series.min()
        elif agg_type == "MAX":
            return series.max()
        elif agg_type == "MEDIAN":
            return series.median() if pd.api.types.is_numeric_dtype(series) else None
        else:
            return None
    except Exception:
        return None

def generate_default_kpis(df: pd.DataFrame, dataset_type: str) -> List[Dict[str, Any]]:
    kpis = []
    
    def add_kpi(name: str, value: Any, description: str, formula: str = "Auto"):
        if value is not None and not pd.isna(value):
            kpis.append({
                "id": str(uuid.uuid4()),
                "name": name,
                "value": _format_value(value),
                "formula": formula,
                "type": dataset_type,
                "created_by": "system",
                "description": description
            })

    if dataset_type == "Sales":
        rev_col = detect_relevant_column(df, ["revenue", "sales", "amount", "total"])
        order_col = detect_relevant_column(df, ["order", "invoice", "transaction", "id"])
        cust_col = detect_relevant_column(df, ["customer", "client", "buyer"])
        prod_col = detect_relevant_column(df, ["product", "item", "sku"])
        reg_col = detect_relevant_column(df, ["region", "country", "city", "state", "location"])
        
        if rev_col:
            add_kpi("Total Revenue", calculate_aggregation(df, rev_col, "SUM"), f"Sum of {rev_col}", f"SUM({rev_col})")
            if order_col:
                total_orders = calculate_aggregation(df, order_col, "COUNT DISTINCT")
                if total_orders and total_orders > 0:
                    tot_rev = calculate_aggregation(df, rev_col, "SUM")
                    if tot_rev is not None:
                        add_kpi("Average Order Value", tot_rev / total_orders, f"Average {rev_col} per {order_col}", f"SUM({rev_col}) / COUNT_DISTINCT({order_col})")
        
        if order_col:
            add_kpi("Total Orders", calculate_aggregation(df, order_col, "COUNT DISTINCT"), f"Unique {order_col}", f"COUNT_DISTINCT({order_col})")
            
        if cust_col:
            add_kpi("Unique Customers", calculate_aggregation(df, cust_col, "COUNT DISTINCT"), f"Unique {cust_col}", f"COUNT_DISTINCT({cust_col})")
            
        if prod_col:
            mode_p = df[prod_col].mode()
            top_prod = mode_p.iloc[0] if not mode_p.empty else "N/A"
            add_kpi("Top Product", top_prod, f"Most frequent {prod_col}", f"MODE({prod_col})")
            
        if reg_col:
            mode_r = df[reg_col].mode()
            top_reg = mode_r.iloc[0] if not mode_r.empty else "N/A"
            add_kpi("Top Region", top_reg, f"Most frequent {reg_col}", f"MODE({reg_col})")

    elif dataset_type == "HR":
        emp_col = detect_relevant_column(df, ["employee", "emp_id", "staff", "name"])
        sal_col = detect_relevant_column(df, ["salary", "pay", "compensation", "wage"])
        dep_col = detect_relevant_column(df, ["department", "team", "division", "dept"])
        att_col = detect_relevant_column(df, ["attrition", "left", "quit", "status"])
        exp_col = detect_relevant_column(df, ["experience", "tenure", "years"])
        
        if emp_col:
            add_kpi("Employee Count", calculate_aggregation(df, emp_col, "COUNT DISTINCT"), f"Unique {emp_col}", f"COUNT_DISTINCT({emp_col})")
        else:
            add_kpi("Total Records", len(df), "Total rows in dataset", "COUNT(*)")
            
        if sal_col:
            add_kpi("Average Salary", calculate_aggregation(df, sal_col, "AVG"), f"Average {sal_col}", f"AVG({sal_col})")
            
        if dep_col:
            add_kpi("Department Count", calculate_aggregation(df, dep_col, "COUNT DISTINCT"), f"Unique {dep_col}", f"COUNT_DISTINCT({dep_col})")
            if sal_col:
                try:
                    highest_dep = df.groupby(dep_col)[sal_col].mean().idxmax()
                    add_kpi("Highest Paying Dept", highest_dep, f"Department with highest average {sal_col}", f"MAX_BY({dep_col}, AVG({sal_col}))")
                except Exception:
                    pass
                    
        if att_col:
            try:
                if df[att_col].dtype == bool:
                    attr_rate = (df[att_col].sum() / len(df)) * 100
                else:
                    attr_rate = (df[att_col].astype(str).str.lower().isin(['yes', '1', 'true', 'left']).sum() / len(df)) * 100
                add_kpi("Attrition Rate", f"{attr_rate:.1f}%", f"Percentage of {att_col}", f"RATE({att_col})")
            except Exception:
                pass
                
        if exp_col and pd.api.types.is_numeric_dtype(df[exp_col]):
            add_kpi("Average Experience", calculate_aggregation(df, exp_col, "AVG"), f"Average {exp_col}", f"AVG({exp_col})")

    elif dataset_type == "Finance":
        inc_col = detect_relevant_column(df, ["income", "revenue", "inflow"])
        exp_col = detect_relevant_column(df, ["expense", "cost", "outflow", "spend"])
        
        if inc_col:
            add_kpi("Total Income", calculate_aggregation(df, inc_col, "SUM"), f"Sum of {inc_col}", f"SUM({inc_col})")
        if exp_col:
            add_kpi("Total Expenses", calculate_aggregation(df, exp_col, "SUM"), f"Sum of {exp_col}", f"SUM({exp_col})")
        if inc_col and exp_col:
            try:
                inc = calculate_aggregation(df, inc_col, "SUM")
                exp = calculate_aggregation(df, exp_col, "SUM")
                if inc is not None and exp is not None:
                    add_kpi("Net Profit", inc - exp, f"{inc_col} minus {exp_col}", f"SUM({inc_col}) - SUM({exp_col})")
                    if inc > 0:
                        add_kpi("Profit Margin", f"{((inc - exp)/inc)*100:.2f}%", "Net Profit / Total Income", f"((INC-EXP)/INC)*100")
            except Exception:
                pass

    elif dataset_type == "Marketing":
        camp_col = detect_relevant_column(df, ["campaign", "ad_name", "ad"])
        lead_col = detect_relevant_column(df, ["lead", "prospect"])
        conv_col = detect_relevant_column(df, ["conversion", "sale"])
        imp_col = detect_relevant_column(df, ["impression", "view"])
        clk_col = detect_relevant_column(df, ["click"])
        chan_col = detect_relevant_column(df, ["channel", "source", "medium"])
        
        if camp_col:
            add_kpi("Total Campaigns", calculate_aggregation(df, camp_col, "COUNT DISTINCT"), f"Unique {camp_col}", f"COUNT_DISTINCT({camp_col})")
        if lead_col:
            agg = "SUM" if pd.api.types.is_numeric_dtype(df[lead_col]) else "COUNT"
            add_kpi("Total Leads", calculate_aggregation(df, lead_col, agg), f"Volume of {lead_col}", f"{agg}({lead_col})")
        if clk_col and imp_col:
            try:
                clicks = calculate_aggregation(df, clk_col, "SUM")
                imps = calculate_aggregation(df, imp_col, "SUM")
                if clicks is not None and imps is not None and imps > 0:
                    add_kpi("CTR", f"{(clicks/imps)*100:.2f}%", f"{clk_col} / {imp_col}", f"(CLICKS/IMPRESSIONS)*100")
            except Exception:
                pass
        if chan_col:
            mode_c = df[chan_col].mode()
            top_chan = mode_c.iloc[0] if not mode_c.empty else "N/A"
            add_kpi("Top Channel", top_chan, f"Most frequent {chan_col}", f"MODE({chan_col})")

    else:
        # General Data Fallback
        add_kpi("Total Rows", len(df), "Count of all records", "COUNT(*)")
        add_kpi("Total Columns", len(df.columns), "Count of attributes", "COL_COUNT")
        num_cols = df.select_dtypes(include=[np.number]).columns
        for col in num_cols[:2]:
            add_kpi(f"Sum of {col}", calculate_aggregation(df, col, "SUM"), f"Summation of {col}", f"SUM({col})")
            add_kpi(f"Avg of {col}", calculate_aggregation(df, col, "AVG"), f"Average of {col}", f"AVG({col})")

    return kpis

def create_manual_kpi(df: pd.DataFrame, name: str, column: str, agg_type: str) -> Dict[str, Any]:
    val = calculate_aggregation(df, column, agg_type)
    if val is None:
        raise ValueError(f"Cannot calculate {agg_type} on column '{column}'. Ensure numeric type for arithmetic aggregations.")
        
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "value": _format_value(val),
        "formula": f"{agg_type}({column})",
        "type": "Custom",
        "created_by": "user",
        "description": f"User defined aggregation: {agg_type} on {column}"
    }

def create_ai_kpi(df: pd.DataFrame, request: str, context: str = "") -> Dict[str, Any]:
    """
    Constructs a data-grounded custom KPI from a natural-language request.
    First attempts to resolve via Google Gemini if an active key is present;
    otherwise falls back to rule-based keyword & schema matching over actual DataFrame data.
    Never fabricates statistics.
    """
    req = request.lower()
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Check if Gemini can parse into structured JSON
    system_prompt = (
        "You are an AI data assistant. Convert the user's KPI request into a JSON structure specifying:\n"
        "{\"name\": string, \"column\": string (must be one of the provided columns), \"agg\": \"SUM\"|\"AVG\"|\"COUNT\"|\"COUNT DISTINCT\"|\"MIN\"|\"MAX\"|\"MEDIAN\", \"description\": string}.\n"
        "Return ONLY pure JSON."
    )
    cols_desc = f"Numeric columns: {num_cols}. Categorical columns: {cat_cols}."
    ai_raw, ai_err = query_gemini(f"Columns: {cols_desc}\nRequest: {request}", system_instruction=system_prompt)
    
    if ai_raw:
        try:
            # Strip markdown code fences if returned
            clean_json = ai_raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            col_target = parsed.get("column")
            agg_target = parsed.get("agg", "SUM").upper()
            if col_target in df.columns:
                val = calculate_aggregation(df, col_target, agg_target)
                if val is not None:
                    return {
                        "id": str(uuid.uuid4()),
                        "name": parsed.get("name", request.title()),
                        "value": _format_value(val),
                        "formula": f"{agg_target}({col_target})",
                        "type": "AI Custom",
                        "created_by": "ai",
                        "description": parsed.get("description", f"AI metric: {agg_target} on {col_target}")
                    }
        except Exception:
            pass

    # Deterministic rule-based calculation over actual dataset
    # 1. Profit Margin / Ratio check
    if "margin" in req or "profit" in req:
        inc_col = detect_relevant_column(df, ["income", "revenue", "sales"])
        exp_col = detect_relevant_column(df, ["expense", "cost"])
        
        if inc_col and exp_col:
            inc = calculate_aggregation(df, inc_col, "SUM")
            exp = calculate_aggregation(df, exp_col, "SUM")
            if inc and inc > 0 and exp is not None:
                val = ((inc - exp) / inc) * 100
                return {
                    "id": str(uuid.uuid4()),
                    "name": "Profit Margin (Calculated)",
                    "value": f"{val:.2f}%",
                    "formula": f"(SUM({inc_col}) - SUM({exp_col})) / SUM({inc_col}) * 100",
                    "type": "Calculated",
                    "created_by": "ai",
                    "description": f"Calculated Net Margin from {inc_col} and {exp_col}"
                }
        elif inc_col:
            val = calculate_aggregation(df, inc_col, "SUM")
            return {
                "id": str(uuid.uuid4()),
                "name": f"Total {inc_col}",
                "value": _format_value(val),
                "formula": f"SUM({inc_col})",
                "type": "Calculated",
                "created_by": "ai",
                "description": f"Sum of {inc_col}"
            }

    # 2. Match exact or partial column names from request
    matched_col = None
    for c in df.columns:
        if c.lower() in req:
            matched_col = c
            break
            
    if not matched_col and num_cols:
        matched_col = num_cols[0]
        
    if not matched_col:
        raise ValueError(f"No suitable column found for query '{request}'. Available columns: {', '.join(df.columns.tolist())}")

    # Determine aggregation function from query
    if any(w in req for w in ["average", "mean", "avg"]):
        agg = "AVG" if pd.api.types.is_numeric_dtype(df[matched_col]) else "COUNT"
    elif any(w in req for w in ["highest", "max", "top", "peak"]):
        agg = "MAX"
    elif any(w in req for w in ["lowest", "min", "bottom"]):
        agg = "MIN"
    elif any(w in req for w in ["unique", "distinct"]):
        agg = "COUNT DISTINCT"
    elif any(w in req for w in ["median"]):
        agg = "MEDIAN" if pd.api.types.is_numeric_dtype(df[matched_col]) else "COUNT"
    else:
        agg = "SUM" if pd.api.types.is_numeric_dtype(df[matched_col]) else "COUNT"
        
    val = calculate_aggregation(df, matched_col, agg)
    if val is None:
        raise ValueError(f"Could not compute {agg} on column '{matched_col}'. Please verify column data type.")
        
    return {
        "id": str(uuid.uuid4()),
        "name": f"{agg.title()} of {matched_col}",
        "value": _format_value(val),
        "formula": f"{agg}({matched_col})",
        "type": "Calculated",
        "created_by": "ai",
        "description": f"Calculated {agg} over {matched_col}"
    }
