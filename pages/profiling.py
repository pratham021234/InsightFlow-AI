import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from services.profiler import (
    get_dataset_overview, get_column_profile, get_missing_analysis,
    get_duplicate_analysis, get_statistical_summary, get_correlation_matrix,
    get_categorical_analysis, get_date_analysis, get_quality_indicators
)
from utils.session_manager import get_active_df, get_original_df

st.set_page_config(page_title="Data Profiling", page_icon="📈", layout="wide")

def main():
    st.title("Data Profiling Engine")
    st.markdown("### Automated Data Quality and Statistical Analysis")
    st.divider()

    original_df = get_original_df()
    cleaned_df = st.session_state.get("cleaned_df")

    if original_df is None:
        st.warning("No dataset found. Please upload or load a sample dataset on the **Upload** page first.")
        st.info("Navigate to the main page from the left sidebar to ingest a dataset.")
        return

    # Dataset version selector if cleaned version exists and differs
    df = original_df
    if cleaned_df is not None and not cleaned_df.equals(original_df):
        ver_col1, ver_col2 = st.columns([2, 2])
        with ver_col1:
            dataset_version = st.radio(
                "Profile Dataset Version:",
                ["Cleaned Dataset (Active)", "Original Uncleaned Dataset"],
                horizontal=True
            )
            df = cleaned_df if "Cleaned" in dataset_version else original_df
        with ver_col2:
            st.caption(f"Currently profiling **{len(df):,} rows** and **{len(df.columns)} columns**.")
    else:
        df = cleaned_df if cleaned_df is not None else original_df

    with st.spinner("Analyzing dataset quality and distributions..."):
        # 1. Dataset Overview
        st.header("1. Dataset Overview")
        overview = get_dataset_overview(df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", f"{overview['Total Rows']:,}")
        col2.metric("Columns", f"{overview['Total Columns']:,}")
        col3.metric("Memory Usage", overview["Memory Usage"])
        
        col4, col5, col6 = st.columns(3)
        col4.metric("Total Missing Values", f"{overview['Total Missing Values']:,}", delta=f"{overview['Missing Ratio']} of cells", delta_color="inverse")
        col5.metric("Duplicate Rows", f"{overview['Duplicate Rows']:,}", delta=overview['Duplicate Ratio'], delta_color="inverse")
        col6.metric("Unique Values Sum", f"{overview['Unique Values']:,}")

        st.divider()

        # 2. Data Quality Dashboard
        st.header("2. Data Quality Health Indicators")
        quality = get_quality_indicators(df)
        
        q_col1, q_col2, q_col3, q_col4 = st.columns(4)
        def display_indicator(label, status, col):
            color = "#27ae60" if status == "Good" else "#f39c12" if status == "Warning" else "#e74c3c"
            col.markdown(
                f"""
                <div style="padding: 12px 16px; border-radius: 8px; border-left: 5px solid {color}; background-color: rgba(128,128,128,0.06); margin-bottom: 10px;">
                    <p style="margin: 0; font-size: 0.85em; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">{label}</p>
                    <span style="color: {color}; font-weight: bold; font-size: 1.3em;">{status}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
        if quality:
            display_indicator("Missing Values", quality["Missing Values"], q_col1)
            display_indicator("Duplicate Rows", quality["Duplicate Rows"], q_col2)
            display_indicator("Type Consistency", quality["Data Type Consistency"], q_col3)
            display_indicator("Memory Footprint", quality["Memory Efficiency"], q_col4)

        st.divider()

        # 3. Data Type Analysis
        st.header("3. Schema & Data Type Breakdown")
        profile_df, type_counts = get_column_profile(df)
        
        col_type1, col_type2 = st.columns([1, 2])
        with col_type1:
            st.markdown("#### Column Counts by Type")
            for k, v in type_counts.items():
                st.write(f"- **{k}:** `{v}`")
        with col_type2:
            st.dataframe(profile_df, use_container_width=True)

        st.divider()

        # 4. Missing Value Analysis
        st.header("4. Missing Value Analysis")
        missing_df = get_missing_analysis(df)
        
        col_miss1, col_miss2 = st.columns([1, 2])
        with col_miss1:
            st.dataframe(missing_df, use_container_width=True)
        with col_miss2:
            has_missing = missing_df[missing_df["Missing Count"] > 0]
            if not has_missing.empty:
                fig_miss = px.bar(
                    has_missing, 
                    x="Column", 
                    y="Missing Count", 
                    title="Missing Values by Column",
                    color="Missing Count",
                    color_continuous_scale="Reds",
                    template="plotly_white"
                )
                st.plotly_chart(fig_miss, use_container_width=True)
            else:
                st.success("Zero missing values detected across all columns.")

        st.divider()

        # 5. Statistical Summary
        st.header("5. Numerical Statistical Summary")
        stats_df = get_statistical_summary(df)
        if not stats_df.empty:
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("No numeric columns found for statistical summary.")

        st.divider()

        # 6. Distribution Analysis
        st.header("6. Numerical Distribution Analysis")
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            limit = min(6, len(num_cols))
            cols_to_plot = num_cols[:limit]
            tabs = st.tabs(cols_to_plot)
            for i, col in enumerate(cols_to_plot):
                with tabs[i]:
                    fig_dist = px.histogram(
                        df, 
                        x=col, 
                        marginal="box",
                        title=f"Distribution of {col}",
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("No numeric columns available for distribution histograms.")

        st.divider()

        # 7. Correlation Analysis
        st.header("7. Correlation Analysis")
        corr_matrix = get_correlation_matrix(df)
        if not corr_matrix.empty and corr_matrix.shape[0] > 1:
            fig_corr = px.imshow(
                corr_matrix, 
                text_auto=True, 
                aspect="auto",
                title="Pearson Correlation Heatmap",
                color_continuous_scale="RdBu_r",
                template="plotly_white"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("At least two numeric columns are required to compute a correlation matrix.")

        st.divider()

        # 8. Categorical Analysis
        st.header("8. Categorical Frequency Analysis")
        cat_analysis = get_categorical_analysis(df)
        if cat_analysis:
            cat_keys = list(cat_analysis.keys())[:8]
            cat_tabs = st.tabs(cat_keys)
            for i, col in enumerate(cat_keys):
                data = cat_analysis[col]
                with cat_tabs[i]:
                    c_col1, c_col2 = st.columns([1, 2])
                    with c_col1:
                        st.write(f"- **Unique Categories:** `{data['Unique Values']}`")
                        st.write(f"- **Top Value:** `{data['Top Category']}`")
                        st.write(f"- **Frequency:** `{data['Frequency']:,}`")
                    with c_col2:
                        vc = data["Value Counts"].head(10).reset_index()
                        vc.columns = [col, "Count"]
                        fig_cat = px.bar(
                            vc, 
                            x=col, 
                            y="Count", 
                            title=f"Top Categories in {col}",
                            template="plotly_white",
                            color="Count",
                            color_continuous_scale="Blues"
                        )
                        st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No categorical text columns found.")

        st.divider()

        # 9. Date Analysis
        st.header("9. Date Column Analysis")
        date_analysis = get_date_analysis(df)
        if date_analysis:
            for col, data in date_analysis.items():
                st.subheader(f"Temporal Field: `{col}`")
                d_c1, d_c2, d_c3 = st.columns(3)
                d_c1.metric("Earliest Date", data['Minimum Date'])
                d_c2.metric("Latest Date", data['Maximum Date'])
                d_c3.metric("Observed Duration", data['Date Range'].split()[0] + " days" if "days" in data['Date Range'] else data['Date Range'])
        else:
            st.info("No date or timestamp columns detected.")

if __name__ == "__main__":
    main()
