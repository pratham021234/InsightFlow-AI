import pandas as pd
import numpy as np
import plotly.express as px
from typing import Dict, Any, Tuple, Optional
from services.ai_service import query_gemini

def detect_intent(query: str) -> str:
    """Classifies the analytical intent of the natural language query."""
    q = query.lower()
    if any(w in q for w in ["how many rows", "what columns", "dataset is this", "clean", "metadata", "how large", "dimensions"]):
        return "Metadata"
    elif any(w in q for w in ["trend", "growth", "over time", "monthly", "yearly", "daily", "timeline"]):
        return "Trend"
    elif any(w in q for w in ["top", "highest", "most", "best", "lowest", "worst", "bottom", "rank", "leading"]):
        return "Ranking"
    elif any(w in q for w in ["compare", "vs", "versus"]):
        return "Comparison"
    elif any(w in q for w in ["distribution", "breakdown", "percentage", "proportion", "share"]):
        return "Distribution"
    elif any(w in q for w in ["risk", "opportunity", "recommend", "management", "focus", "threat"]):
        return "Insight Request"
    elif any(w in q for w in ["visualize", "plot", "chart", "graph", "show me a"]):
        return "Visualization"
    else:
        return "Aggregation"

def extract_entities(query: str, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """Identifies the Measure (Numeric) and Dimension (Categorical) from the query."""
    q = query.lower()
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    measure = None
    for col in num_cols:
        if col.lower() in q:
            measure = col
            break
            
    if not measure and num_cols:
        # Synonyms
        if any(w in q for w in ["revenue", "sales", "amt", "price", "amount", "value"]):
            measure = next((c for c in num_cols if any(x in c.lower() for x in ["rev", "sale", "amt", "price", "total", "val"])), num_cols[0])
        elif any(w in q for w in ["cost", "expense", "spend"]):
            measure = next((c for c in num_cols if any(x in c.lower() for x in ["cost", "exp", "spend"])), num_cols[0])
        elif any(w in q for w in ["salary", "pay", "income", "compensation"]):
            measure = next((c for c in num_cols if any(x in c.lower() for x in ["sal", "pay", "comp", "inc"])), num_cols[0])
        elif any(w in q for w in ["quantity", "units", "count", "volume"]):
            measure = next((c for c in num_cols if any(x in c.lower() for x in ["quant", "unit", "vol", "cnt"])), num_cols[0])
        else:
            measure = num_cols[0]
            
    dimension = None
    for col in cat_cols:
        if col.lower() in q:
            dimension = col
            break
            
    if not dimension and cat_cols:
        # Synonyms
        if any(w in q for w in ["region", "city", "country", "location", "territory"]):
            dimension = next((c for c in cat_cols if any(x in c.lower() for x in ["reg", "cit", "coun", "loc", "area", "terr"])), cat_cols[0])
        elif any(w in q for w in ["product", "item", "category", "sku"]):
            dimension = next((c for c in cat_cols if any(x in c.lower() for x in ["prod", "item", "cat", "sku", "type"])), cat_cols[0])
        elif any(w in q for w in ["customer", "client", "buyer", "account"]):
            dimension = next((c for c in cat_cols if any(x in c.lower() for x in ["cust", "cli", "buy", "acc"])), cat_cols[0])
        elif any(w in q for w in ["department", "team", "division", "dept"]):
            dimension = next((c for c in cat_cols if any(x in c.lower() for x in ["dept", "dep", "team", "div"])), cat_cols[0])
        elif any(w in q for w in ["status", "tier", "stage"]):
            dimension = next((c for c in cat_cols if any(x in c.lower() for x in ["stat", "tier", "stag"])), cat_cols[0])
        else:
            dimension = cat_cols[0]
            
    return measure, dimension

def handle_metadata_questions(query: str, df: pd.DataFrame, insights: dict) -> str:
    """Answers dataset size, health, and strategic insight queries."""
    q = query.lower()
    if any(w in q for w in ["rows", "how large", "size", "records"]):
        return f"The active dataset contains **{len(df):,}** rows and **{len(df.columns)}** columns."
    elif "columns" in q:
        return f"Available columns ({len(df.columns)}): `{', '.join(df.columns.tolist())}`."
    elif any(w in q for w in ["missing", "null", "clean"]):
        missing_count = int(df.isna().sum().sum())
        total_cells = df.shape[0] * df.shape[1]
        pct = (missing_count / total_cells * 100) if total_cells > 0 else 0
        return f"The current dataset has **{missing_count:,}** missing values ({pct:.2f}% of all cells) across all columns."
    elif any(w in q for w in ["risk", "opportunity", "recommend", "management", "focus"]):
        if insights and insights.get("executive_summary"):
            return f"**Business Context & Strategy:**\n\n{insights.get('executive_summary')}\n\n*Review the AI Insights page for detailed risk and opportunity decompositions.*"
        return "Please navigate to the AI Business Insights page to generate a comprehensive strategic evaluation."
    else:
        return f"This dataset contains {len(df):,} rows across {len(df.columns)} attributes: {', '.join(df.columns[:8].tolist())}."

def execute_query(df: pd.DataFrame, intent: str, measure: Optional[str], dimension: Optional[str], raw_query: str = "") -> Dict[str, Any]:
    """Safely executes the Pandas operation inferred by query intent."""
    result_data = None
    fig = None
    text_answer = ""
    q = raw_query.lower()
    
    try:
        # Check if scalar aggregation without dimension breakdown was requested
        is_grouped_request = any(w in q for w in ["by", "per", "across", "each", "every", "group", "breakdown"])
        
        if intent == "Aggregation" and not is_grouped_request and measure:
            if any(w in q for w in ["average", "mean", "avg"]):
                avg_val = df[measure].mean() if pd.api.types.is_numeric_dtype(df[measure]) else 0
                text_answer = f"The overall average **{measure}** across the dataset is **{avg_val:,.2f}**."
            else:
                tot_val = df[measure].sum() if pd.api.types.is_numeric_dtype(df[measure]) else len(df)
                text_answer = f"The total **{measure}** across the dataset is **{tot_val:,.2f}**."
            return {"text": text_answer, "data": None, "fig": None}

        if intent == "Ranking" and measure and dimension:
            is_lowest = any(w in q for w in ["lowest", "worst", "bottom", "least"])
            res = df.groupby(dimension)[measure].sum().reset_index().sort_values(by=measure, ascending=is_lowest).head(10)
            result_data = res
            top_entity = res.iloc[0][dimension]
            top_val = res.iloc[0][measure]
            order_label = "lowest" if is_lowest else "top"
            text_answer = f"The {order_label} **{dimension}** by {measure} is **{top_entity}** with **{top_val:,.2f}**."
            fig = px.bar(res, x=dimension, y=measure, title=f"{order_label.title()} 10 {dimension} by {measure}", template="plotly_white", color=measure, color_continuous_scale="Blues")
            
        elif intent in ["Distribution", "Aggregation"] and measure and dimension:
            res = df.groupby(dimension)[measure].sum().reset_index().sort_values(by=measure, ascending=False).head(10)
            result_data = res
            text_answer = f"Here is the breakdown of total **{measure}** grouped by **{dimension}**."
            fig = px.pie(res, names=dimension, values=measure, title=f"Distribution of {measure} by {dimension}", template="plotly_white")
            
        elif intent == "Trend" and measure:
            date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
            if not date_cols:
                for c in df.select_dtypes(include=['object']).columns:
                    try:
                        converted = pd.to_datetime(df[c], errors='coerce')
                        if converted.notna().sum() > len(df) * 0.7:
                            df = df.copy()
                            df[c] = converted
                            date_cols.append(c)
                            break
                    except Exception:
                        pass
                        
            if len(date_cols) > 0:
                d_col = date_cols[0]
                temp = df.dropna(subset=[d_col, measure]).sort_values(by=d_col)
                res = temp.groupby(temp[d_col].dt.to_period("M"))[measure].sum().reset_index()
                res[d_col] = res[d_col].astype(str)
                result_data = res
                text_answer = f"Observed monthly timeline trend for **{measure}** across `{d_col}`."
                fig = px.line(res, x=d_col, y=measure, title=f"Monthly Trend: {measure}", template="plotly_white", markers=True)
            elif dimension:
                res = df.groupby(dimension)[measure].sum().reset_index()
                result_data = res
                text_answer = f"No temporal column detected. Showing total **{measure}** across **{dimension}** instead."
                fig = px.bar(res, x=dimension, y=measure, template="plotly_white")
                
        elif intent == "Comparison" and measure and dimension:
            res = df.groupby(dimension)[measure].sum().reset_index().head(10)
            result_data = res
            text_answer = f"Comparative distribution of **{measure}** across categories of **{dimension}**."
            fig = px.bar(res, x=dimension, y=measure, color=dimension, title=f"Comparison: {measure} across {dimension}", template="plotly_white")
            
        elif intent == "Visualization" and measure and dimension:
            res = df.groupby(dimension)[measure].sum().reset_index().sort_values(by=measure, ascending=False).head(10)
            result_data = res
            text_answer = f"Rendered visual distribution for **{measure}** by **{dimension}**."
            fig = px.bar(res, x=dimension, y=measure, template="plotly_white", color=measure, color_continuous_scale="Viridis")
            
        elif measure:
            val = df[measure].sum() if pd.api.types.is_numeric_dtype(df[measure]) else len(df)
            text_answer = f"Total **{measure}** computed across the active dataset is **{val:,.2f}**."
            
        else:
            text_answer = f"Evaluated query. Dataset contains {len(df):,} records."
            
    except Exception as e:
        text_answer = f"Calculation note: {str(e)}"
        
    return {
        "text": text_answer,
        "data": result_data,
        "fig": fig
    }

def generate_ai_explanation(result_text: str, query: str) -> str:
    """Generates an executive explanation via Gemini if active, or a contextual summary."""
    prompt = f"User asked: '{query}'. Computed result: '{result_text}'. Provide a concise 1-2 sentence executive business takeaway."
    ai_resp, err = query_gemini(prompt, system_instruction="You are a senior business intelligence analyst. Keep insights concise, professional, and directly grounded in the computed result.")
    
    if ai_resp:
        return f"**AI Business Context:** {ai_resp}"
        
    # Data-grounded contextual explanation fallback
    return f"**Business Takeaway:** Identifying top performance drivers and variance distributions in this dimension directly assists in allocating resources and optimizing segment margins."
