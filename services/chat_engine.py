import pandas as pd
import numpy as np
import plotly.express as px
from typing import Dict, Any, Tuple

def detect_intent(query: str) -> str:
    """Classifies the analytical intent of the natural language query."""
    q = query.lower()
    if any(w in q for w in ["how many rows", "what columns", "dataset is this", "clean", "metadata", "how large"]):
        return "Metadata"
    elif any(w in q for w in ["trend", "growth", "over time", "monthly", "yearly", "daily"]):
        return "Trend"
    elif any(w in q for w in ["top", "highest", "most", "best", "lowest", "worst", "bottom"]):
        return "Ranking"
    elif any(w in q for w in ["compare", "vs", "versus"]):
        return "Comparison"
    elif any(w in q for w in ["distribution", "breakdown", "percentage"]):
        return "Distribution"
    elif any(w in q for w in ["risk", "opportunity", "recommend", "management", "focus"]):
        return "Insight Request"
    elif any(w in q for w in ["visualize", "plot", "chart", "graph", "show me a"]):
        return "Visualization"
    else:
        return "Aggregation"

def extract_entities(query: str, df: pd.DataFrame) -> Tuple[str, str]:
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
        # Fallbacks for common synonyms
        if "revenue" in q or "sales" in q or "profit" in q or "value" in q:
            measure = next((c for c in num_cols if any(x in c.lower() for x in ["rev", "sale", "prof", "amt", "total", "val"])), num_cols[0])
        elif "salary" in q or "pay" in q or "income" in q:
            measure = next((c for c in num_cols if any(x in c.lower() for x in ["sal", "pay", "comp", "inc"])), num_cols[0])
        else:
            measure = num_cols[0]
            
    dimension = None
    for col in cat_cols:
        if col.lower() in q:
            dimension = col
            break
            
    if not dimension and cat_cols:
        # Fallbacks for common synonyms
        if "region" in q or "city" in q or "country" in q or "location" in q:
            dimension = next((c for c in cat_cols if any(x in c.lower() for x in ["reg", "cit", "coun", "loc", "area"])), cat_cols[0])
        elif "product" in q or "item" in q or "category" in q:
            dimension = next((c for c in cat_cols if any(x in c.lower() for x in ["prod", "item", "cat", "type"])), cat_cols[0])
        elif "customer" in q or "client" in q or "buyer" in q:
            dimension = next((c for c in cat_cols if any(x in c.lower() for x in ["cust", "cli", "buy"])), cat_cols[0])
        elif "department" in q or "team" in q or "division" in q:
            dimension = next((c for c in cat_cols if any(x in c.lower() for x in ["dept", "dep", "team", "div"])), cat_cols[0])
        else:
            dimension = cat_cols[0]
            
    return measure, dimension

def handle_metadata_questions(query: str, df: pd.DataFrame, insights: dict) -> str:
    """Answers dataset size, health, and strategic insight queries."""
    q = query.lower()
    if "rows" in q or "how large" in q or "size" in q:
        return f"The dataset contains {len(df):,} rows and {len(df.columns)} columns."
    elif "columns" in q:
        return f"Available columns are: {', '.join(df.columns.tolist())}."
    elif "missing" in q or "clean" in q:
        return f"The current dataset has {df.isna().sum().sum()} missing values across all columns."
    elif "risk" in q or "opportunity" in q or "management" in q or "focus" in q:
        if insights and insights.get("executive_summary"):
            return f"**Business Insight:**\n\n{insights.get('executive_summary')}\n\n*Please review the AI Insights page for a detailed breakdown of risks and opportunities.*"
        return "Please run the AI Business Insights module first to generate strategic metadata."
    else:
        return "This appears to be a metadata question, but I couldn't map it to a specific dataset property."

def execute_query(df: pd.DataFrame, intent: str, measure: str, dimension: str) -> Dict[str, Any]:
    """Safely executes the Pandas operation inferred by the query intent."""
    result_data = None
    fig = None
    text_answer = ""
    
    try:
        if intent == "Ranking":
            res = df.groupby(dimension)[measure].sum().reset_index().sort_values(by=measure, ascending=False).head(10)
            result_data = res
            top_entity = res.iloc[0][dimension]
            top_val = res.iloc[0][measure]
            text_answer = f"The top {dimension} by {measure} is **{top_entity}** with a total of **{top_val:,.2f}**."
            fig = px.bar(res, x=dimension, y=measure, title=f"Top 10 {dimension} by {measure}", template="plotly_white")
            
        elif intent in ["Distribution", "Aggregation"]:
            res = df.groupby(dimension)[measure].mean().reset_index().sort_values(by=measure, ascending=False).head(10)
            result_data = res
            text_answer = f"Here is the average {measure} broken down by {dimension}."
            fig = px.pie(res, names=dimension, values=measure, title=f"Distribution of Average {measure} by {dimension}", template="plotly_white")
            
        elif intent == "Trend":
            date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns
            if len(date_cols) > 0:
                d_col = date_cols[0]
                temp = df.dropna(subset=[d_col, measure])
                # Safe period aggregation
                res = temp.groupby(temp[d_col].dt.to_period("M"))[measure].sum().reset_index()
                res[d_col] = res[d_col].astype(str)
                result_data = res
                text_answer = f"Here is the monthly trend for {measure}."
                fig = px.line(res, x=d_col, y=measure, title=f"Trend of {measure} over {d_col}", template="plotly_white")
            else:
                res = df.groupby(dimension)[measure].sum().reset_index()
                result_data = res
                text_answer = f"No date column found. Showing total {measure} by {dimension} instead."
                fig = px.bar(res, x=dimension, y=measure, template="plotly_white")
                
        elif intent == "Comparison":
            res = df.groupby(dimension)[measure].sum().reset_index()
            result_data = res
            text_answer = f"Comparing total {measure} across {dimension}."
            fig = px.bar(res, x=dimension, y=measure, color=dimension, title=f"Comparison of {measure} by {dimension}", template="plotly_white")
            
        elif intent == "Visualization":
            res = df.groupby(dimension)[measure].sum().reset_index().sort_values(by=measure, ascending=False).head(10)
            result_data = res
            text_answer = f"Generated a visualization for {measure} grouped by {dimension}."
            fig = px.bar(res, x=dimension, y=measure, template="plotly_white")
            
        else:
            val = df[measure].sum()
            text_answer = f"The total {measure} across the dataset is **{val:,.2f}**."
            
    except Exception as e:
        text_answer = f"An error occurred while calculating the result: {str(e)}"
        
    return {
        "text": text_answer,
        "data": result_data,
        "fig": fig
    }

def generate_ai_explanation(result_text: str, query: str) -> str:
    """Mock LLM finalizing the response with business context."""
    return f"**AI Explanation:** Based on your query regarding '{query}', the data shows that {result_text.lower().replace('the top', 'the leading').replace('here is', 'we can observe')} This is significant because identifying and optimizing these metrics directly impacts overall efficiency within this domain."
