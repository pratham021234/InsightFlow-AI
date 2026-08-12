import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import uuid
import datetime
from typing import Dict, List, Any

def generate_auto_charts(df: pd.DataFrame) -> List[Dict[str, Any]]:
    charts = []
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
    
    # 1. Numeric Charts
    if num_cols:
        for col in num_cols[:2]:
            fig = px.histogram(df, x=col, title=f"Distribution of {col}", template="plotly_white")
            charts.append({"id": str(uuid.uuid4()), "title": f"Histogram: {col}", "fig": fig, "type": "Histogram", "created_by": "system", "timestamp": datetime.datetime.now().isoformat()})
            
            fig_box = px.box(df, y=col, title=f"Box Plot of {col}", template="plotly_white")
            charts.append({"id": str(uuid.uuid4()), "title": f"Box Plot: {col}", "fig": fig_box, "type": "Box Plot", "created_by": "system", "timestamp": datetime.datetime.now().isoformat()})
            
        if len(num_cols) >= 2:
            fig_corr = px.imshow(df[num_cols].corr(), text_auto=True, title="Correlation Heatmap", template="plotly_white", color_continuous_scale="RdBu_r")
            charts.append({"id": str(uuid.uuid4()), "title": "Numeric Correlation", "fig": fig_corr, "type": "Heatmap", "created_by": "system", "timestamp": datetime.datetime.now().isoformat()})
            
            corr_mat = df[num_cols].corr().abs()
            for col in corr_mat.columns:
                if col in corr_mat.index:
                    corr_mat.loc[col, col] = 0.0
            if not corr_mat.empty and not corr_mat.isna().all().all():
                max_corr_idx = corr_mat.unstack().idxmax()
                if isinstance(max_corr_idx, tuple) and len(max_corr_idx) == 2:
                    c1, c2 = max_corr_idx
                    fig_scat = px.scatter(df, x=c1, y=c2, title=f"Scatter: {c1} vs {c2}", template="plotly_white")
                    charts.append({"id": str(uuid.uuid4()), "title": f"Scatter: Strongest Correlation", "fig": fig_scat, "type": "Scatter", "created_by": "system", "timestamp": datetime.datetime.now().isoformat()})

    # 2. Categorical Charts
    if cat_cols:
        for col in cat_cols[:2]:
            vc = df[col].value_counts().reset_index().head(10)
            vc.columns = [col, 'Count']
            fig_bar = px.bar(vc, x=col, y='Count', title=f"Top 10 Categories in {col}", template="plotly_white")
            charts.append({"id": str(uuid.uuid4()), "title": f"Bar Chart: {col}", "fig": fig_bar, "type": "Bar", "created_by": "system", "timestamp": datetime.datetime.now().isoformat()})
            
            fig_pie = px.pie(vc, names=col, values='Count', title=f"Distribution of {col}", template="plotly_white")
            charts.append({"id": str(uuid.uuid4()), "title": f"Pie Chart: {col}", "fig": fig_pie, "type": "Pie", "created_by": "system", "timestamp": datetime.datetime.now().isoformat()})
            
    # 3. Date Charts
    if date_cols and num_cols:
        d_col = date_cols[0]
        n_col = num_cols[0]
        temp = df.dropna(subset=[d_col, n_col]).sort_values(by=d_col)
        fig_line = px.line(temp, x=d_col, y=n_col, title=f"Trend of {n_col} over {d_col}", template="plotly_white")
        charts.append({"id": str(uuid.uuid4()), "title": f"Trend Analysis", "fig": fig_line, "type": "Line", "created_by": "system", "timestamp": datetime.datetime.now().isoformat()})
        
    return charts

def create_custom_chart(df: pd.DataFrame, chart_type: str, x_axis: str, y_axis: str, agg: str, color_by: str = None) -> Any:
    temp_df = df.copy()
    
    try:
        if agg != "None" and y_axis:
            group_cols = [x_axis]
            if color_by and color_by != "None" and color_by in temp_df.columns:
                group_cols.append(color_by)
                
            if agg == "SUM":
                temp_df = temp_df.groupby(group_cols, as_index=False)[y_axis].sum(numeric_only=True)
            elif agg == "AVG":
                temp_df = temp_df.groupby(group_cols, as_index=False)[y_axis].mean(numeric_only=True)
            elif agg == "COUNT":
                temp_df = temp_df.groupby(group_cols, as_index=False)[y_axis].count()
            elif agg == "MIN":
                temp_df = temp_df.groupby(group_cols, as_index=False)[y_axis].min(numeric_only=True)
            elif agg == "MAX":
                temp_df = temp_df.groupby(group_cols, as_index=False)[y_axis].max(numeric_only=True)
            elif agg == "MEDIAN":
                temp_df = temp_df.groupby(group_cols, as_index=False)[y_axis].median(numeric_only=True)
                
            if temp_df.empty or y_axis not in temp_df.columns:
                raise ValueError(f"Cannot perform {agg} aggregation on column '{y_axis}'. Please ensure it is numeric.")
    except Exception as e:
        raise ValueError(f"Aggregation error: {str(e)}. Try selecting a numeric column for the Y Axis.")
            
    title = f"{chart_type} of {y_axis} by {x_axis}" if y_axis else f"{chart_type} of {x_axis}"
    
    kwargs = {"template": "plotly_white", "title": title}
    if color_by and color_by != "None" and color_by in temp_df.columns:
        kwargs["color"] = color_by

    if chart_type == "Bar":
        fig = px.bar(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Line":
        fig = px.line(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Scatter":
        fig = px.scatter(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Pie":
        if y_axis:
            fig = px.pie(temp_df, names=x_axis, values=y_axis, **kwargs)
        else:
            vc = temp_df[x_axis].value_counts().reset_index()
            vc.columns = [x_axis, 'Count']
            fig = px.pie(vc, names=x_axis, values='Count', **kwargs)
    elif chart_type == "Histogram":
        fig = px.histogram(temp_df, x=x_axis, **kwargs)
    elif chart_type == "Box Plot":
        fig = px.box(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Area":
        fig = px.area(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Heatmap":
        if y_axis:
            fig = px.density_heatmap(temp_df, x=x_axis, y=y_axis, **kwargs)
        else:
            raise ValueError("Heatmap requires X and Y axis.")
    elif chart_type == "Treemap":
        if y_axis:
            # Handle zeros/negatives for Treemap gently
            temp_df = temp_df[temp_df[y_axis] > 0]
            fig = px.treemap(temp_df, path=[x_axis], values=y_axis, **kwargs)
        else:
            raise ValueError("Treemap requires X and Y axis.")
    elif chart_type == "Sunburst":
        if y_axis:
            temp_df = temp_df[temp_df[y_axis] > 0]
            fig = px.sunburst(temp_df, path=[x_axis], values=y_axis, **kwargs)
        else:
            raise ValueError("Sunburst requires X and Y axis.")
    else:
        fig = px.bar(temp_df, x=x_axis, y=y_axis, **kwargs)
        
    return fig

def create_ai_chart(df: pd.DataFrame, prompt: str) -> Dict[str, Any]:
    """
    Mocks an LLM returning a visualization JSON payload based on natural language parsing.
    In a fully live Gemini-connected environment, we would send the schema and prompt 
    to retrieve strict JSON representing chart_type, x_axis, y_axis, etc.
    """
    p = prompt.lower()
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
    
    if not num_cols:
        raise ValueError("No numeric columns available for AI to graph.")
        
    y = num_cols[0]
    
    if "trend" in p or "growth" in p or "over time" in p or "monthly" in p:
        if date_cols:
            x = date_cols[0]
            ctype = "Line"
            agg = "SUM"
        else:
            raise ValueError("Trend requested but no date column found.")
    elif "distribution" in p:
        x = cat_cols[0] if cat_cols else num_cols[0]
        ctype = "Histogram" if not cat_cols else "Pie"
        agg = "COUNT"
    elif "compare" in p or "across" in p or "by" in p:
        x = cat_cols[0] if cat_cols else num_cols[0]
        ctype = "Bar"
        agg = "SUM"
    else:
        x = cat_cols[0] if cat_cols else num_cols[0]
        ctype = "Bar"
        agg = "AVG"
        
    fig = create_custom_chart(df, ctype, x, y, agg)
    
    return {
        "id": str(uuid.uuid4()),
        "title": f"AI Generated: {prompt.title()}",
        "fig": fig,
        "type": ctype,
        "created_by": "ai",
        "timestamp": datetime.datetime.now().isoformat()
    }
