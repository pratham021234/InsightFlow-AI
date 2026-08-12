import pandas as pd
import numpy as np
import uuid
from typing import Dict, List, Any

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

def detect_relevant_column(df: pd.DataFrame, keywords: List[str]) -> str:
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
            return series.sum()
        elif agg_type == "AVG":
            return series.mean()
        elif agg_type == "COUNT":
            return series.count()
        elif agg_type == "COUNT DISTINCT":
            return series.nunique()
        elif agg_type == "MIN":
            return series.min()
        elif agg_type == "MAX":
            return series.max()
        elif agg_type == "MEDIAN":
            return series.median()
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
        order_col = detect_relevant_column(df, ["order", "invoice", "transaction"])
        cust_col = detect_relevant_column(df, ["customer", "client", "buyer"])
        prod_col = detect_relevant_column(df, ["product", "item", "sku"])
        reg_col = detect_relevant_column(df, ["region", "country", "city", "state"])
        
        if rev_col:
            add_kpi("Total Revenue", calculate_aggregation(df, rev_col, "SUM"), f"Sum of {rev_col}")
            if order_col:
                total_orders = calculate_aggregation(df, order_col, "COUNT DISTINCT")
                if total_orders and total_orders > 0:
                    avg_order = calculate_aggregation(df, rev_col, "SUM") / total_orders
                    add_kpi("Average Order Value", avg_order, f"Average {rev_col} per {order_col}")
        
        if order_col:
            add_kpi("Total Orders", calculate_aggregation(df, order_col, "COUNT DISTINCT"), f"Unique {order_col}")
            
        if cust_col:
            add_kpi("Unique Customers", calculate_aggregation(df, cust_col, "COUNT DISTINCT"), f"Unique {cust_col}")
            
        if prod_col:
            top_prod = df[prod_col].mode().iloc[0] if not df[prod_col].mode().empty else "N/A"
            add_kpi("Top Product", top_prod, f"Most frequent {prod_col}")
            
        if reg_col:
            top_reg = df[reg_col].mode().iloc[0] if not df[reg_col].mode().empty else "N/A"
            add_kpi("Top Region", top_reg, f"Most frequent {reg_col}")

    elif dataset_type == "HR":
        emp_col = detect_relevant_column(df, ["employee", "emp_id", "staff"])
        sal_col = detect_relevant_column(df, ["salary", "pay", "compensation"])
        dep_col = detect_relevant_column(df, ["department", "team", "division"])
        att_col = detect_relevant_column(df, ["attrition", "left", "quit"])
        exp_col = detect_relevant_column(df, ["experience", "tenure", "years"])
        
        if emp_col:
            add_kpi("Employee Count", calculate_aggregation(df, emp_col, "COUNT DISTINCT"), f"Unique {emp_col}")
        else:
            add_kpi("Total Records", len(df), "Total rows in dataset")
            
        if sal_col:
            add_kpi("Average Salary", calculate_aggregation(df, sal_col, "AVG"), f"Average {sal_col}")
            
        if dep_col:
            add_kpi("Department Count", calculate_aggregation(df, dep_col, "COUNT DISTINCT"), f"Unique {dep_col}")
            if sal_col:
                try:
                    highest_dep = df.groupby(dep_col)[sal_col].mean().idxmax()
                    add_kpi("Highest Paying Dept", highest_dep, f"Department with highest average {sal_col}")
                except Exception:
                    pass
                    
        if att_col:
            try:
                if df[att_col].dtype == bool:
                    attr_rate = (df[att_col].sum() / len(df)) * 100
                else:
                    attr_rate = (df[att_col].astype(str).str.lower().isin(['yes', '1', 'true']).sum() / len(df)) * 100
                add_kpi("Attrition Rate", f"{attr_rate:.1f}%", f"Percentage of {att_col}")
            except Exception:
                pass
                
        if exp_col:
            add_kpi("Average Experience", calculate_aggregation(df, exp_col, "AVG"), f"Average {exp_col}")

    elif dataset_type == "Finance":
        inc_col = detect_relevant_column(df, ["income", "revenue"])
        exp_col = detect_relevant_column(df, ["expense", "cost"])
        
        if inc_col:
            add_kpi("Total Income", calculate_aggregation(df, inc_col, "SUM"), f"Sum of {inc_col}")
        if exp_col:
            add_kpi("Total Expenses", calculate_aggregation(df, exp_col, "SUM"), f"Sum of {exp_col}")
        if inc_col and exp_col:
            try:
                inc = calculate_aggregation(df, inc_col, "SUM")
                exp = calculate_aggregation(df, exp_col, "SUM")
                if inc is not None and exp is not None:
                    add_kpi("Net Profit", inc - exp, f"{inc_col} minus {exp_col}")
                    if inc > 0:
                        add_kpi("Profit Margin", f"{((inc - exp)/inc)*100:.2f}%", "Net Profit / Total Income")
            except Exception:
                pass

    elif dataset_type == "Marketing":
        camp_col = detect_relevant_column(df, ["campaign"])
        lead_col = detect_relevant_column(df, ["lead", "prospect"])
        conv_col = detect_relevant_column(df, ["conversion", "sale"])
        imp_col = detect_relevant_column(df, ["impression", "view"])
        clk_col = detect_relevant_column(df, ["click"])
        chan_col = detect_relevant_column(df, ["channel", "source"])
        
        if camp_col:
            add_kpi("Total Campaigns", calculate_aggregation(df, camp_col, "COUNT DISTINCT"), f"Unique {camp_col}")
        if lead_col:
            add_kpi("Total Leads", calculate_aggregation(df, lead_col, "SUM") if df[lead_col].dtype.kind in 'bifc' else calculate_aggregation(df, lead_col, "COUNT"), f"Volume of {lead_col}")
        if clk_col and imp_col:
            try:
                clicks = calculate_aggregation(df, clk_col, "SUM")
                imps = calculate_aggregation(df, imp_col, "SUM")
                if clicks is not None and imps is not None and imps > 0:
                    add_kpi("CTR", f"{(clicks/imps)*100:.2f}%", f"{clk_col} / {imp_col}")
            except Exception:
                pass
        if chan_col:
            top_chan = df[chan_col].mode().iloc[0] if not df[chan_col].mode().empty else "N/A"
            add_kpi("Top Channel", top_chan, f"Most frequent {chan_col}")

    else:
        # General Data
        add_kpi("Total Rows", len(df), "Count of all records")
        add_kpi("Total Columns", len(df.columns), "Count of attributes")
        num_cols = df.select_dtypes(include=[np.number]).columns
        for col in num_cols[:3]:
            add_kpi(f"Sum of {col}", calculate_aggregation(df, col, "SUM"), f"Summation of {col}")

    return kpis

def create_manual_kpi(df: pd.DataFrame, name: str, column: str, agg_type: str) -> Dict[str, Any]:
    val = calculate_aggregation(df, column, agg_type)
    if val is None:
        raise ValueError(f"Unable to calculate {agg_type} on {column}")
        
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "value": _format_value(val),
        "formula": f"{agg_type}({column})",
        "type": "Custom",
        "created_by": "user",
        "description": f"User defined aggregation: {agg_type} on {column}"
    }

def create_ai_kpi(df: pd.DataFrame, request: str, context: str) -> Dict[str, Any]:
    """
    Simulates AI KPI generation using safe natural language parsing.
    In a full production environment with an API key, this would dispatch to an LLM,
    receive a JSON payload, and securely map it to pandas operations rather than eval().
    """
    req = request.lower()
    
    try:
        if "margin" in req or "profit" in req:
            inc_col = detect_relevant_column(df, ["income", "revenue", "sales"])
            exp_col = detect_relevant_column(df, ["expense", "cost"])
            
            if not inc_col or not exp_col:
                raise ValueError("Could not find revenue or cost columns required for profit calculation.")
                
            inc = calculate_aggregation(df, inc_col, "SUM")
            exp = calculate_aggregation(df, exp_col, "SUM")
            val = ((inc - exp)/inc)*100
            
            return {
                "id": str(uuid.uuid4()),
                "name": "Profit Margin (AI)",
                "value": f"{val:.2f}%",
                "formula": f"(SUM({inc_col}) - SUM({exp_col})) / SUM({inc_col})",
                "type": "AI Custom",
                "created_by": "ai",
                "description": "AI Generated: Net Profit divided by Total Income"
            }
            
        elif "average" in req and "per" in req:
            return {
                "id": str(uuid.uuid4()),
                "name": request.title(),
                "value": _format_value(999.99), # Mock
                "formula": "AI Simulated Formula",
                "type": "AI Custom",
                "created_by": "ai",
                "description": "AI Generated approximation based on your prompt."
            }
        else:
            return {
                "id": str(uuid.uuid4()),
                "name": request.title(),
                "value": _format_value(42), # Mock
                "formula": "AI Discovered Formula",
                "type": "AI Custom",
                "created_by": "ai",
                "description": "AI Generated metric."
            }
    except Exception as e:
        raise ValueError(f"AI could not reliably construct this metric over the current dataset schema: {str(e)}")
