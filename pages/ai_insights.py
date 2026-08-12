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

st.set_page_config(page_title="AI Business Insights", page_icon="💡", layout="wide")

def display_insight_card(insight):
    color = "red" if insight['priority'] == "High" else "orange" if insight['priority'] == "Medium" else "green"
    st.markdown(
        f"""
        <div style="padding: 15px; border-radius: 5px; border-left: 5px solid {color}; background-color: rgba(128,128,128,0.05); margin-bottom: 10px; box-shadow: 1px 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #333;">{insight['title']}</h4>
                <span style="color: {color}; font-weight: bold; font-size: 0.8em; border: 1px solid {color}; padding: 2px 8px; border-radius: 12px; background-color: rgba(255,255,255,0.8);">{insight['priority']}</span>
            </div>
            <p style="margin: 10px 0 0 0; color: #555; font-size: 0.95em;">{insight['description']}</p>
            <p style="margin: 5px 0 0 0; color: #888; font-size: 0.8em; font-style: italic;">Category: {insight['category']}</p>
        </div>
        """, unsafe_allow_html=True
    )

def main():
    st.title("AI Business Insights Engine")
    st.markdown("### Executive Summaries, Strategic Risks, and Actionable Recommendations")
    st.divider()

    df = st.session_state.get("cleaned_df", st.session_state.get("original_df"))
    if df is None:
        st.warning("No dataset found. Please upload a dataset first.")
        return
        
    dataset_type = st.session_state.get("dataset_type", "General Dataset")
    kpis = st.session_state.get("kpis", [])
    
    with st.spinner("Compiling Executive Insights..."):
        if "executive_summary" not in st.session_state:
            st.session_state["executive_summary"] = generate_executive_summary(df, dataset_type, kpis)
            st.session_state["insights_findings"] = generate_key_findings(df, dataset_type)
            st.session_state["insights_trends"] = analyze_trends(df)
            st.session_state["insights_anomalies"] = detect_anomalies(df)
            st.session_state["insights_risks"] = identify_risks(dataset_type)
            st.session_state["insights_opps"] = identify_opportunities(dataset_type)
            st.session_state["insights_recs"] = generate_recommendations(dataset_type)
            st.session_state["insights_kpi_interp"] = interpret_kpis(kpis)

    # 1. Executive Summary
    st.header("1. Executive Summary")
    st.info(st.session_state["executive_summary"])
    st.divider()

    # Category Filter
    st.markdown("### Insight Explorer")
    categories = ["All", "Revenue", "Customers", "Products", "Operations", "Employees", "Finance", "Marketing"]
    selected_cat = st.radio("Filter Insights by Category:", categories, horizontal=True)
    st.divider()
    
    def filter_insights(data_list):
        if selected_cat == "All":
            return data_list
        return [d for d in data_list if d.get("category") == selected_cat]

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Key Findings", "Trends & Anomalies", "Risks", "Opportunities", "Recommendations", "KPI Interpretations", "Ask AI"
    ])

    with tab1:
        st.subheader("Key Findings")
        f_data = filter_insights(st.session_state["insights_findings"])
        if not f_data: st.write("No findings in this category.")
        for f in f_data: display_insight_card(f)

    with tab2:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("Trend Analysis")
            t_data = filter_insights(st.session_state["insights_trends"])
            if not t_data: st.write("No trends in this category.")
            for t in t_data: display_insight_card(t)
        with col_t2:
            st.subheader("Anomaly Detection")
            a_data = filter_insights(st.session_state["insights_anomalies"])
            if not a_data: st.write("No anomalies in this category.")
            for a in a_data: display_insight_card(a)

    with tab3:
        st.subheader("Risk Identification")
        r_data = filter_insights(st.session_state["insights_risks"])
        if not r_data: st.write("No risks in this category.")
        for r in r_data: display_insight_card(r)

    with tab4:
        st.subheader("Business Opportunities")
        o_data = filter_insights(st.session_state["insights_opps"])
        if not o_data: st.write("No opportunities in this category.")
        for o in o_data: display_insight_card(o)

    with tab5:
        st.subheader("Actionable Recommendations")
        rec_data = filter_insights(st.session_state["insights_recs"])
        if not rec_data: st.write("No recommendations in this category.")
        for rec in rec_data: display_insight_card(rec)

    with tab6:
        st.subheader("KPI Interpretations")
        interps = st.session_state["insights_kpi_interp"]
        if not interps:
            st.write("No KPIs generated yet to interpret.")
        for interp in interps:
            with st.expander(interp["kpi_name"]):
                st.markdown(f"**Business Meaning:** {interp['meaning']}")
                st.markdown(f"**Impact:** {interp['impact']}")

    with tab7:
        st.subheader("AI Insight Generation (Gemini LLM)")
        st.write("Send the entire analytical context to Gemini for a highly specific, unstructured JSON evaluation.")
        if st.button("Generate Advanced AI Insights", type="primary"):
            with st.spinner("Querying LLM..."):
                ai_resp = generate_ai_insights(dataset_type, kpis, "Full Context")
                st.json(ai_resp)

    st.divider()
    st.header("Export Insights")
    st.write("Download the complete executive report as a text document.")
    
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
        label="Download Report (TXT)",
        data=export_txt,
        file_name="InsightFlow_Executive_Report.txt",
        mime="text/plain"
    )

if __name__ == "__main__":
    main()
