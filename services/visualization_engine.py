import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import uuid
import datetime
import json
from typing import Dict, List, Any, Optional
from services.ai_service import query_gemini

def generate_auto_charts(df: pd.DataFrame) -> List[Dict[str, Any]]:
    charts = []
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
    
    # Check if object columns can be treated as dates
    if not date_cols:
        for c in cat_cols:
            try:
                converted = pd.to_datetime(df[c], errors='coerce')
                if converted.notna().sum() > len(df) * 0.7:
                    df = df.copy()
                    df[c] = converted
                    date_cols.append(c)
                    break
            except Exception:
                pass

    # 1. Numeric Charts
    if num_cols:
        for col in num_cols[:2]:
            fig = px.histogram(df, x=col, marginal="box", title=f"Distribution of {col}", template="plotly_white")
            charts.append({
                "id": str(uuid.uuid4()),
                "title": f"Distribution: {col}",
                "fig": fig,
                "type": "Histogram",
                "created_by": "system",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            
        if len(num_cols) >= 2:
            corr_mat = df[num_cols].corr()
            fig_corr = px.imshow(corr_mat, text_auto=True, title="Correlation Matrix Heatmap", template="plotly_white", color_continuous_scale="RdBu_r")
            charts.append({
                "id": str(uuid.uuid4()),
                "title": "Numeric Correlation Heatmap",
                "fig": fig_corr,
                "type": "Heatmap",
                "created_by": "system",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            
            # Strongest correlation scatter
            corr_abs = corr_mat.abs()
            for col in corr_abs.columns:
                corr_abs.loc[col, col] = 0.0
            if not corr_abs.empty and not corr_abs.isna().all().all():
                c1, c2 = corr_abs.unstack().idxmax()
                fig_scat = px.scatter(df, x=c1, y=c2, title=f"Scatter: {c1} vs {c2}", template="plotly_white")
                charts.append({
                    "id": str(uuid.uuid4()),
                    "title": f"Scatter: {c1} vs {c2}",
                    "fig": fig_scat,
                    "type": "Scatter",
                    "created_by": "system",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })

    # 2. Categorical Charts
    if cat_cols:
        for col in cat_cols[:2]:
            vc = df[col].value_counts().head(10).reset_index()
            vc.columns = [col, 'Count']
            fig_bar = px.bar(vc, x=col, y='Count', title=f"Top Categories in {col}", template="plotly_white", color="Count", color_continuous_scale="Blues")
            charts.append({
                "id": str(uuid.uuid4()),
                "title": f"Frequency: {col}",
                "fig": fig_bar,
                "type": "Bar",
                "created_by": "system",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            
            fig_pie = px.pie(vc, names=col, values='Count', title=f"Proportion of {col}", template="plotly_white")
            charts.append({
                "id": str(uuid.uuid4()),
                "title": f"Proportion: {col}",
                "fig": fig_pie,
                "type": "Pie",
                "created_by": "system",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            
    # 3. Date Time-Series Charts
    if date_cols and num_cols:
        d_col = date_cols[0]
        n_col = num_cols[0]
        temp = df.dropna(subset=[d_col, n_col]).sort_values(by=d_col)
        if not temp.empty:
            fig_line = px.line(temp, x=d_col, y=n_col, title=f"Trend of {n_col} Over Time", template="plotly_white")
            charts.append({
                "id": str(uuid.uuid4()),
                "title": f"Trend: {n_col} Timeline",
                "fig": fig_line,
                "type": "Line",
                "created_by": "system",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        
    return charts

def create_custom_chart(df: pd.DataFrame, chart_type: str, x_axis: str, y_axis: Optional[str] = None, agg: str = "None", color_by: Optional[str] = None) -> Any:
    temp_df = df.copy()
    
    if not x_axis or x_axis not in temp_df.columns:
        raise ValueError("Please select a valid X Axis column.")
        
    if color_by == "None" or color_by == "":
        color_by = None

    try:
        if agg != "None" and y_axis and y_axis in temp_df.columns:
            group_cols = [x_axis]
            if color_by and color_by in temp_df.columns and color_by != x_axis:
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
                raise ValueError(f"Cannot perform {agg} aggregation on '{y_axis}'. Please select a numeric column.")
    except Exception as e:
        raise ValueError(f"Aggregation error: {str(e)}")
            
    title = f"{chart_type} Chart: {y_axis} by {x_axis}" if y_axis else f"{chart_type} Chart of {x_axis}"
    kwargs = {"template": "plotly_white", "title": title}
    if color_by and color_by in temp_df.columns:
        kwargs["color"] = color_by

    if chart_type == "Bar":
        return px.bar(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Line":
        return px.line(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Scatter":
        return px.scatter(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Pie":
        if y_axis:
            return px.pie(temp_df, names=x_axis, values=y_axis, **kwargs)
        else:
            vc = temp_df[x_axis].value_counts().reset_index()
            vc.columns = [x_axis, 'Count']
            return px.pie(vc, names=x_axis, values='Count', **kwargs)
    elif chart_type == "Histogram":
        return px.histogram(temp_df, x=x_axis, y=y_axis if y_axis else None, **kwargs)
    elif chart_type == "Box Plot":
        return px.box(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Area":
        return px.area(temp_df, x=x_axis, y=y_axis, **kwargs)
    elif chart_type == "Heatmap":
        if y_axis:
            return px.density_heatmap(temp_df, x=x_axis, y=y_axis, **kwargs)
        else:
            raise ValueError("Density Heatmap requires both X and Y axis columns.")
    elif chart_type == "Treemap":
        if y_axis:
            temp_df = temp_df[temp_df[y_axis] > 0]
            return px.treemap(temp_df, path=[x_axis], values=y_axis, **kwargs)
        else:
            raise ValueError("Treemap requires a positive numeric Y axis column.")
    elif chart_type == "Sunburst":
        if y_axis:
            temp_df = temp_df[temp_df[y_axis] > 0]
            return px.sunburst(temp_df, path=[x_axis], values=y_axis, **kwargs)
        else:
            raise ValueError("Sunburst requires a positive numeric Y axis column.")
    else:
        return px.bar(temp_df, x=x_axis, y=y_axis, **kwargs)

def create_ai_chart(df: pd.DataFrame, prompt: str) -> Dict[str, Any]:
    """
    Parses a natural-language visualization request.
    Leverages Google Gemini if connected, otherwise uses intelligent heuristic mapping
    over available numeric and categorical fields.
    """
    p = prompt.lower()
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
    
    # Try Gemini structure parsing first
    system_instruction = (
        "You are an expert data visualization assistant. Convert the user's chart request into JSON:\n"
        "{\"chart_type\": \"Bar\"|\"Line\"|\"Scatter\"|\"Pie\"|\"Histogram\"|\"Box Plot\"|\"Area\",\n"
        " \"x_axis\": string (must be in columns),\n"
        " \"y_axis\": string or null,\n"
        " \"agg\": \"SUM\"|\"AVG\"|\"COUNT\"|\"None\"}\n"
        "Return pure JSON."
    )
    cols_ctx = f"Numeric: {num_cols}. Categorical: {cat_cols}. Date: {date_cols}."
    ai_resp, _ = query_gemini(f"Columns: {cols_ctx}\nPrompt: {prompt}", system_instruction=system_instruction)
    
    if ai_resp:
        try:
            clean_json = ai_resp.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            ctype = parsed.get("chart_type", "Bar")
            x = parsed.get("x_axis")
            y = parsed.get("y_axis")
            agg = parsed.get("agg", "None")
            if x in df.columns:
                fig = create_custom_chart(df, ctype, x, y if y in df.columns else None, agg)
                return {
                    "id": str(uuid.uuid4()),
                    "title": f"AI Chart: {prompt.title()}",
                    "fig": fig,
                    "type": ctype,
                    "created_by": "ai",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
        except Exception:
            pass

    # Heuristic mapping over actual dataset columns
    matched_x = None
    matched_y = None
    
    for c in df.columns:
        if c.lower() in p:
            if c in num_cols and not matched_y:
                matched_y = c
            elif not matched_x:
                matched_x = c

    if "trend" in p or "over time" in p or "timeline" in p:
        ctype = "Line"
        x = date_cols[0] if date_cols else (cat_cols[0] if cat_cols else df.columns[0])
        y = matched_y if matched_y else (num_cols[0] if num_cols else None)
        agg = "SUM" if y else "None"
    elif "distribution" in p or "spread" in p:
        ctype = "Histogram"
        x = matched_y if matched_y else (num_cols[0] if num_cols else df.columns[0])
        y = None
        agg = "None"
    elif "proportion" in p or "share" in p or "percentage" in p or "breakdown" in p:
        ctype = "Pie"
        x = matched_x if matched_x else (cat_cols[0] if cat_cols else df.columns[0])
        y = matched_y if matched_y else (num_cols[0] if num_cols else None)
        agg = "SUM" if y else "None"
    elif "scatter" in p or "correlation" in p or "vs" in p:
        ctype = "Scatter"
        x = matched_x if (matched_x and matched_x in num_cols) else (num_cols[0] if num_cols else df.columns[0])
        y = matched_y if (matched_y and matched_y != x) else (num_cols[1] if len(num_cols) > 1 else None)
        agg = "None"
    else:
        ctype = "Bar"
        x = matched_x if matched_x else (cat_cols[0] if cat_cols else df.columns[0])
        y = matched_y if matched_y else (num_cols[0] if num_cols else None)
        agg = "SUM" if y else "None"
        
    fig = create_custom_chart(df, ctype, x, y, agg)
    return {
        "id": str(uuid.uuid4()),
        "title": f"AI Chart: {prompt.title()}",
        "fig": fig,
        "type": ctype,
        "created_by": "ai",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
