import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from services.profiler import (
    get_dataset_overview, get_column_profile, get_missing_analysis,
    get_duplicate_analysis, get_statistical_summary, get_correlation_matrix,
    get_categorical_analysis, get_date_analysis, get_quality_indicators
)

st.set_page_config(page_title="Data Profiling", page_icon="📈", layout="wide")

def main():
    st.title("Data Profiling Engine")
    st.markdown("### Automated Data Quality and Statistical Analysis")
    st.divider()

    if "original_df" not in st.session_state or st.session_state["original_df"] is None:
        st.warning("No dataset found. Please upload a dataset on the Upload page first.")
        return

    df = st.session_state["original_df"]

    with st.spinner("Analyzing dataset..."):
        # 1. Dataset Overview
        st.header("1. Dataset Overview")
        overview = get_dataset_overview(df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", f"{overview['Total Rows']:,}")
        col2.metric("Columns", f"{overview['Total Columns']:,}")
        col3.metric("Memory Usage", overview["Memory Usage"])
        
        col4, col5, col6 = st.columns(3)
        col4.metric("Missing Values", f"{overview['Total Missing Values']:,}")
        col5.metric("Duplicate Rows", f"{overview['Duplicate Rows']:,}")
        col6.metric("Unique Values", f"{overview['Unique Values']:,}")

        st.divider()

        # 2. Data Type Analysis
        st.header("2. Data Type Analysis")
        profile_df, type_counts = get_column_profile(df)
        
        col_type1, col_type2 = st.columns([1, 2])
        with col_type1:
            st.markdown("#### Summary")
            for k, v in type_counts.items():
                st.write(f"**{k}:** {v}")
        with col_type2:
            st.dataframe(profile_df, use_container_width=True)

        st.divider()

        # 3. Missing Value Analysis
        st.header("3. Missing Value Analysis")
        missing_df = get_missing_analysis(df)
        
        col_miss1, col_miss2 = st.columns([1, 2])
        with col_miss1:
            st.dataframe(missing_df, use_container_width=True)
        with col_miss2:
            if missing_df['Missing Count'].sum() > 0:
                fig_miss = px.bar(
                    missing_df[missing_df["Missing Count"] > 0], 
                    x="Column", 
                    y="Missing Count", 
                    title="Missing Values by Column"
                )
                st.plotly_chart(fig_miss, use_container_width=True)
            else:
                st.success("No missing values found in the dataset.")

        st.divider()

        # 4. Duplicate Analysis
        st.header("4. Duplicate Analysis")
        dup_analysis = get_duplicate_analysis(df)
        st.write(f"**Total Duplicate Rows:** {dup_analysis['Total Duplicate Rows']}")
        st.write(f"**Duplicate Percentage:** {dup_analysis['Duplicate Percentage']}")

        st.divider()

        # 5. Statistical Summary
        st.header("5. Statistical Summary")
        stats_df = get_statistical_summary(df)
        if not stats_df.empty:
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("No numeric columns found for statistical summary.")

        st.divider()

        # 6. Distribution Analysis
        st.header("6. Distribution Analysis")
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            limit = min(5, len(num_cols))
            cols_to_plot = num_cols[:limit]
            tabs = st.tabs(cols_to_plot)
            for i, col in enumerate(cols_to_plot):
                with tabs[i]:
                    fig_dist = px.histogram(df, x=col, title=f"Distribution of {col}")
                    st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("No numeric columns found for distribution analysis.")

        st.divider()

        # 7. Correlation Analysis
        st.header("7. Correlation Analysis")
        corr_matrix = get_correlation_matrix(df)
        if not corr_matrix.empty:
            fig_corr = px.imshow(
                corr_matrix, 
                text_auto=True, 
                aspect="auto",
                title="Correlation Heatmap",
                color_continuous_scale="RdBu_r"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("No numeric columns found for correlation analysis.")

        st.divider()

        # 8. Categorical Analysis
        st.header("8. Categorical Analysis")
        cat_analysis = get_categorical_analysis(df)
        if cat_analysis:
            cat_tabs = st.tabs(list(cat_analysis.keys())[:10]) # Limit to 10 for UI
            for i, (col, data) in enumerate(list(cat_analysis.items())[:10]):
                with cat_tabs[i]:
                    st.write(f"**Unique Values:** {data['Unique Values']}")
                    st.write(f"**Top Category:** {data['Top Category']}")
                    st.write(f"**Frequency:** {data['Frequency']}")
                    
                    vc = data["Value Counts"].head(10).reset_index()
                    vc.columns = [col, "Count"]
                    fig_cat = px.bar(vc, x=col, y="Count", title=f"Top 10 Categories in {col}")
                    st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No categorical columns found.")

        st.divider()

        # 9. Date Column Analysis
        st.header("9. Date Column Analysis")
        date_analysis = get_date_analysis(df)
        if date_analysis:
            for col, data in date_analysis.items():
                st.subheader(f"Column: {col}")
                st.write(f"**Minimum Date:** {data['Minimum Date']}")
                st.write(f"**Maximum Date:** {data['Maximum Date']}")
                st.write(f"**Date Range:** {data['Date Range']}")
                
                temp_df = df.copy()
                temp_df[col] = pd.to_datetime(temp_df[col], errors='coerce')
                temp_df = temp_df.dropna(subset=[col])
                if not temp_df.empty:
                    fig_date = px.histogram(temp_df, x=col, title=f"Timeline of {col}")
                    st.plotly_chart(fig_date, use_container_width=True)
        else:
            st.info("No date columns detected.")

        st.divider()

        # 10. Data Quality Dashboard
        st.header("10. Data Quality Dashboard")
        quality = get_quality_indicators(df)
        
        q_col1, q_col2, q_col3, q_col4 = st.columns(4)
        
        def display_indicator(label, status, col):
            color = "green" if status == "Good" else "orange" if status == "Warning" else "red"
            col.markdown(
                f"""
                <div style="padding: 10px; border-radius: 5px; border-left: 5px solid {color}; background-color: rgba(128,128,128,0.1); margin-bottom: 10px;">
                    <h4 style="margin-top: 0;">{label}</h4>
                    <span style="color: {color}; font-weight: bold; font-size: 1.2em;">{status}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
        if quality:
            display_indicator("Missing Values", quality["Missing Values"], q_col1)
            display_indicator("Duplicate Rows", quality["Duplicate Rows"], q_col2)
            display_indicator("Data Type Consistency", quality["Data Type Consistency"], q_col3)
            display_indicator("Memory Efficiency", quality["Memory Efficiency"], q_col4)

if __name__ == "__main__":
    main()
