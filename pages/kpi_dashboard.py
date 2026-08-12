import streamlit as st
import pandas as pd
from services.kpi_engine import (
    generate_default_kpis,
    create_manual_kpi,
    create_ai_kpi
)

st.set_page_config(page_title="KPI Dashboard Engine", page_icon="🎯", layout="wide")

def main():
    st.title("Dynamic KPI Engine")
    st.markdown("### Monitor, Create, and Ask AI for Custom Business Metrics")
    st.divider()

    df = st.session_state.get("cleaned_df", st.session_state.get("original_df"))
    
    if df is None:
        st.warning("No dataset found. Please upload and clean a dataset first.")
        return
        
    dataset_type = st.session_state.get("dataset_type", "General Dataset")
    
    # Initialize KPI Store
    if "kpis" not in st.session_state:
        with st.spinner("Generating Domain-Specific Default KPIs..."):
            st.session_state["kpis"] = generate_default_kpis(df, dataset_type)
            
    # 1. KPI Overview
    st.header("1. KPI Dashboard Overview")
    kpis = st.session_state["kpis"]
    
    if not kpis:
        st.info("No KPIs available. Create one below.")
    else:
        cols = st.columns(min(len(kpis), 4) if len(kpis) > 0 else 1)
        for i, kpi in enumerate(kpis):
            col = cols[i % 4]
            source_icon = "🤖" if kpi["created_by"] == "ai" else "👤" if kpi["created_by"] == "user" else "⚙️"
            col.markdown(
                f"""
                <div style="padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 15px; background-color: rgba(128,128,128,0.05); box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                    <p style="margin: 0; color: #888; font-size: 0.9em;">{source_icon} {kpi['type']}</p>
                    <h3 style="margin: 5px 0;">{kpi['name']}</h3>
                    <h2 style="margin: 0; color: #007bff;">{kpi['value']}</h2>
                    <p style="margin: 10px 0 0 0; font-size: 0.8em; color: #666;">{kpi['description']}</p>
                </div>
                """, unsafe_allow_html=True
            )
            
    st.divider()

    st.header("KPI Management & Builders")
    tab1, tab2, tab3 = st.tabs(["Manual KPI Builder", "AI KPI Builder", "KPI Repository"])
    
    # 2. Manual Builder
    with tab1:
        st.subheader("Create Manual KPI")
        with st.form("manual_kpi_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                kpi_name = st.text_input("KPI Name", placeholder="e.g. Total Revenue")
            with c2:
                all_cols = df.columns.tolist()
                kpi_col = st.selectbox("Column Selection", all_cols)
            with c3:
                agg_type = st.selectbox("Aggregation Type", ["SUM", "AVG", "COUNT", "COUNT DISTINCT", "MIN", "MAX", "MEDIAN"])
                
            submitted = st.form_submit_button("Create KPI", type="primary")
            if submitted:
                if not kpi_name:
                    st.error("Please enter a KPI Name.")
                else:
                    try:
                        new_kpi = create_manual_kpi(df, kpi_name, kpi_col, agg_type)
                        st.session_state["kpis"].append(new_kpi)
                        st.success(f"KPI '{kpi_name}' created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating KPI: {str(e)}")
                        
    # 3. AI Builder
    with tab2:
        st.subheader("AI-Powered KPI Builder")
        st.write("Describe the metric you want to calculate in natural language.")
        with st.form("ai_kpi_form"):
            ai_request = st.text_area("What would you like to measure?", placeholder="e.g. 'Calculate the Profit Margin' or 'Average Revenue Per Customer'")
            
            ai_submitted = st.form_submit_button("Generate with AI", type="primary")
            if ai_submitted:
                if not ai_request:
                    st.error("Please enter a request.")
                else:
                    try:
                        context = f"Domain: {dataset_type}"
                        ai_kpi = create_ai_kpi(df, ai_request, context)
                        st.session_state["kpis"].append(ai_kpi)
                        st.success(f"AI successfully generated KPI: '{ai_kpi['name']}'")
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI Generation failed: {str(e)}")
                        
    # 4. Repository
    with tab3:
        st.subheader("KPI Repository")
        if not kpis:
            st.write("No KPIs exist.")
        else:
            kpi_df = pd.DataFrame(kpis)
            display_df = kpi_df[["name", "value", "formula", "created_by", "description"]].copy()
            st.dataframe(display_df, use_container_width=True)
            
            st.markdown("### Manage KPIs")
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                kpi_to_del = st.selectbox("Select KPI to Delete", [k['name'] for k in kpis])
            with col_del2:
                st.write("")
                st.write("")
                if st.button("Delete Selected KPI"):
                    st.session_state["kpis"] = [k for k in kpis if k['name'] != kpi_to_del]
                    st.success("Deleted!")
                    st.rerun()

if __name__ == "__main__":
    main()
