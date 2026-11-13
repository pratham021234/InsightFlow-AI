import streamlit as st
import pandas as pd
from services.kpi_engine import (
    generate_default_kpis,
    create_manual_kpi,
    create_ai_kpi
)
from utils.session_manager import get_active_df

st.set_page_config(page_title="KPI Dashboard Engine", page_icon="🎯", layout="wide")

def main():
    st.title("Dynamic KPI Engine")
    st.markdown("### Domain-Aware Business Metrics, Custom Calculations & Natural Language Queries")
    st.divider()

    df = get_active_df()
    if df is None:
        st.warning("No dataset found. Please upload or load a sample dataset on the **Upload** page first.")
        st.info("Navigate to the main page from the left sidebar to ingest a dataset.")
        return
        
    dataset_type = st.session_state.get("dataset_type", "General Dataset")
    
    # Initialize KPI Store
    if st.session_state.get("kpis") is None:
        with st.spinner("Generating Domain-Specific Default KPIs..."):
            st.session_state["kpis"] = generate_default_kpis(df, dataset_type)
            
    # 1. KPI Overview
    st.header("1. KPI Executive Summary")
    st.caption(f"Domain context: **{dataset_type}** | Active records: **{len(df):,}**")
    kpis = st.session_state["kpis"]
    
    if not kpis:
        st.info("No KPIs currently configured. Create a custom metric below.")
    else:
        # Display in 4-column responsive grid
        cols = st.columns(4)
        for i, kpi in enumerate(kpis):
            col = cols[i % 4]
            source_icon = "🤖" if kpi.get("created_by") == "ai" else "👤" if kpi.get("created_by") == "user" else "⚙️"
            source_label = "AI Formula" if kpi.get("created_by") == "ai" else "Custom User" if kpi.get("created_by") == "user" else "Domain Standard"
            col.markdown(
                f"""
                <div style="padding: 16px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 16px; background-color: rgba(128,128,128,0.04); box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.75em; text-transform: uppercase; color: #777; font-weight: 600;">{kpi.get('type', 'Metric')}</span>
                        <span style="font-size: 0.75em; color: #555; background: #eee; padding: 2px 6px; border-radius: 4px;">{source_icon} {source_label}</span>
                    </div>
                    <h4 style="margin: 0 0 6px 0; color: #2c3e50; font-size: 1.05em;">{kpi['name']}</h4>
                    <h2 style="margin: 0 0 8px 0; color: #1a73e8; font-size: 1.8em;">{kpi['value']}</h2>
                    <p style="margin: 0; font-size: 0.8em; color: #666; line-height: 1.3;">{kpi.get('description', '')}</p>
                </div>
                """, unsafe_allow_html=True
            )
            
    st.divider()

    st.header("2. Metric Builders & Repository")
    tab1, tab2, tab3 = st.tabs(["Manual KPI Builder", "AI Metric Builder", "KPI Repository"])
    
    # 2. Manual Builder
    with tab1:
        st.subheader("Manual Aggregation Builder")
        with st.form("manual_kpi_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                kpi_name = st.text_input("Metric Title", placeholder="e.g. Total Revenue")
            with c2:
                all_cols = df.columns.tolist()
                kpi_col = st.selectbox("Column Target", all_cols)
            with c3:
                agg_type = st.selectbox("Aggregation Function", ["SUM", "AVG", "COUNT", "COUNT DISTINCT", "MIN", "MAX", "MEDIAN"])
                
            submitted = st.form_submit_button("Calculate & Add Metric", type="primary")
            if submitted:
                if not kpi_name:
                    st.error("Please specify a Metric Title.")
                else:
                    try:
                        new_kpi = create_manual_kpi(df, kpi_name, kpi_col, agg_type)
                        st.session_state["kpis"].append(new_kpi)
                        st.success(f"KPI '{kpi_name}' calculated and added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error calculating metric: {str(e)}")
                        
    # 3. AI Builder
    with tab2:
        st.subheader("Natural Language Metric Generator")
        st.write("Specify what you want to measure in plain English (e.g. *'Average Cost'*, *'Total Revenue'*, or *'Profit Margin'*).")
        with st.form("ai_kpi_form"):
            ai_request = st.text_input("Metric Query", placeholder="e.g. Calculate profit margin from revenue and cost")
            ai_submitted = st.form_submit_button("Generate Metric", type="primary")
            if ai_submitted:
                if not ai_request:
                    st.error("Please enter a query.")
                else:
                    try:
                        ai_kpi = create_ai_kpi(df, ai_request, f"Domain: {dataset_type}")
                        st.session_state["kpis"].append(ai_kpi)
                        st.success(f"Successfully calculated: **{ai_kpi['name']}** = **{ai_kpi['value']}**")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not construct metric: {str(e)}")
                        
    # 4. Repository
    with tab3:
        st.subheader("Active Metric Inventory")
        if not kpis:
            st.info("No active KPIs.")
        else:
            kpi_df = pd.DataFrame(kpis)
            display_cols = [c for c in ["name", "value", "formula", "created_by", "description"] if c in kpi_df.columns]
            st.dataframe(kpi_df[display_cols], use_container_width=True)
            
            st.markdown("#### Delete Metric")
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                kpi_to_del = st.selectbox("Select metric to remove", [k['name'] for k in kpis])
            with col_del2:
                st.write("")
                st.write("")
                if st.button("Delete Metric", type="secondary"):
                    st.session_state["kpis"] = [k for k in kpis if k['name'] != kpi_to_del]
                    st.success(f"Removed '{kpi_to_del}'!")
                    st.rerun()

if __name__ == "__main__":
    main()
