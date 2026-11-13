import streamlit as st
import pandas as pd
from services.insights_engine import (
    generate_executive_summary,
    generate_key_findings,
    analyze_trends,
    detect_anomalies,
    identify_risks,
    identify_opportunities,
    generate_recommendations,
    interpret_kpis,
    generate_ai_insights,
    format_export_text
)
from services.ai_service import check_gemini_status
from utils.session_manager import get_active_df

st.set_page_config(page_title="AI Business Insights", page_icon="💡", layout="wide")

def display_insight_card(insight):
    priority = insight.get('priority', 'Info')
    color = "#e74c3c" if priority == "High" else "#f39c12" if priority == "Medium" else "#27ae60"
    st.markdown(
        f"""
        <div style="padding: 14px 18px; border-radius: 8px; border-left: 5px solid {color}; background-color: rgba(128,128,128,0.04); margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #2c3e50; font-size: 1.05em;">{insight.get('title', 'Insight')}</h4>
                <span style="color: {color}; font-weight: 700; font-size: 0.75em; border: 1px solid {color}; padding: 2px 8px; border-radius: 12px; background-color: rgba(255,255,255,0.9);">{priority.upper()}</span>
            </div>
            <p style="margin: 8px 0 4px 0; color: #444; font-size: 0.95em; line-height: 1.4;">{insight.get('description', '')}</p>
            <p style="margin: 4px 0 0 0; color: #888; font-size: 0.8em;">Dimension Category: <i>{insight.get('category', 'General')}</i></p>
        </div>
        """, unsafe_allow_html=True
    )

def main():
    st.title("AI Business Insights Engine")
    st.markdown("### Executive Narrative, Trend Audits, Strategic Risks & Prescriptive Guidance")
    st.divider()

    df = get_active_df()
    if df is None:
        st.warning("No dataset found. Please upload or load a sample dataset on the **Upload** page first.")
        st.info("Navigate to the main page from the left sidebar to ingest a dataset.")
        return
        
    dataset_type = st.session_state.get("dataset_type", "General Dataset")
    kpis = st.session_state.get("kpis", [])
    
    with st.spinner("Synthesizing strategic business observations..."):
        if st.session_state.get("executive_summary") is None:
            st.session_state["executive_summary"] = generate_executive_summary(df, dataset_type, kpis)
            st.session_state["insights_findings"] = generate_key_findings(df, dataset_type)
            st.session_state["insights_trends"] = analyze_trends(df)
            st.session_state["insights_anomalies"] = detect_anomalies(df)
            st.session_state["insights_risks"] = identify_risks(dataset_type, df)
            st.session_state["insights_opps"] = identify_opportunities(dataset_type, df)
            st.session_state["insights_recs"] = generate_recommendations(dataset_type, df)
            st.session_state["insights_kpi_interp"] = interpret_kpis(kpis)

    # 1. Executive Summary
    st.header("1. Executive Summary")
    st.info(st.session_state["executive_summary"])
    st.divider()

    # Category Filter
    st.markdown("### Insight Explorer")
    categories = ["All", "Revenue", "Customers", "Products", "Operations", "Employees", "Finance", "Marketing"]
    selected_cat = st.radio("Filter Insights by Operational Dimension:", categories, horizontal=True)
    st.divider()
    
    def filter_insights(data_list):
        if not data_list:
            return []
        if selected_cat == "All":
            return data_list
        return [d for d in data_list if d.get("category") == selected_cat]

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Key Findings", "Trends & Anomalies", "Risks", "Opportunities", "Recommendations", "KPI Definitions", "Ask AI"
    ])

    with tab1:
        st.subheader("Data-Grounded Key Findings")
        f_data = filter_insights(st.session_state["insights_findings"])
        if not f_data:
            st.info(f"No specific findings in category '{selected_cat}'. Switch filter to 'All' to view all findings.")
        for f in f_data:
            display_insight_card(f)

    with tab2:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("Trend Trajectory")
            t_data = filter_insights(st.session_state["insights_trends"])
            if not t_data:
                st.info("No trends in this category.")
            for t in t_data:
                display_insight_card(t)
        with col_t2:
            st.subheader("Anomalies & Outliers")
            a_data = filter_insights(st.session_state["insights_anomalies"])
            if not a_data:
                st.info("No anomalies in this category.")
            for a in a_data:
                display_insight_card(a)

    with tab3:
        st.subheader("Business & Operational Risks")
        r_data = filter_insights(st.session_state["insights_risks"])
        if not r_data:
            st.info("No risks in this category.")
        for r in r_data:
            display_insight_card(r)

    with tab4:
        st.subheader("Strategic Growth Opportunities")
        o_data = filter_insights(st.session_state["insights_opps"])
        if not o_data:
            st.info("No opportunities in this category.")
        for o in o_data:
            display_insight_card(o)

    with tab5:
        st.subheader("Actionable Recommendations")
        rec_data = filter_insights(st.session_state["insights_recs"])
        if not rec_data:
            st.info("No recommendations in this category.")
        for rec in rec_data:
            display_insight_card(rec)

    with tab6:
        st.subheader("KPI Definitions & Strategic Impact")
        interps = st.session_state["insights_kpi_interp"]
        if not interps:
            st.info("No KPIs have been calculated yet. Visit the **KPI Dashboard** to generate metrics.")
        for interp in interps:
            with st.expander(f"Metric: {interp['kpi_name']}"):
                st.markdown(f"**Business Meaning:** {interp['meaning']}")
                st.markdown(f"**Organizational Impact:** {interp['impact']}")

    with tab7:
        st.subheader("Google Gemini LLM Evaluation")
        is_ready, status_msg = check_gemini_status()
        
        if is_ready:
            st.success(f"**Status:** {status_msg}")
            st.write("Click below to synthesize a multi-point executive assessment using Google Gemini.")
            if st.button("Generate Advanced AI Assessment", type="primary"):
                with st.spinner("Synthesizing analysis via Gemini..."):
                    ai_resp = generate_ai_insights(dataset_type, kpis, f"Rows: {len(df)}, Cols: {len(df.columns)}")
                    st.json(ai_resp)
        else:
            st.warning(f"**LLM Service Status:** {status_msg}")
            st.caption("The application operates with deterministic, data-grounded algorithms. To enable live Gemini synthesis, provide a valid API key in `.streamlit/secrets.toml`:")
            st.code('GEMINI_API_KEY = "AIzaSy..."', language="toml")
            if st.button("Preview Structured Analytical Context", type="secondary"):
                fallback_insights = generate_ai_insights(dataset_type, kpis, "Local Evaluation")
                st.json(fallback_insights)

    st.divider()
    st.header("2. Export Executive Report")
    st.write("Download this complete narrative assessment as a formatted text document.")
    
    export_txt = format_export_text(
        st.session_state["executive_summary"],
        st.session_state["insights_findings"],
        st.session_state["insights_trends"],
        st.session_state["insights_anomalies"],
        st.session_state["insights_risks"],
        st.session_state["insights_opps"],
        st.session_state["insights_recs"],
        st.session_state["insights_kpi_interp"]
    )
    
    st.download_button(
        label="Download Executive Text Report (.txt)",
        data=export_txt,
        file_name="InsightFlow_Executive_Report.txt",
        mime="text/plain",
        use_container_width=True
    )

if __name__ == "__main__":
    main()
