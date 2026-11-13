import streamlit as st
import pandas as pd
from services.visualization_engine import (
    generate_auto_charts,
    create_custom_chart,
    create_ai_chart
)
from utils.session_manager import get_active_df

st.set_page_config(page_title="Visual Analytics", page_icon="📊", layout="wide")

def display_chart_card(chart_dict, stable_key: str):
    st.markdown(f"#### {chart_dict['title']}")
    st.plotly_chart(
        chart_dict['fig'], 
        use_container_width=True, 
        config={'displaylogo': False, 'modeBarButtonsToRemove': ['lasso2d']},
        key=stable_key
    )
    st.caption(f"**Type:** {chart_dict['type']} | **Source:** {chart_dict.get('created_by', 'system').title()} | **Timestamp:** {chart_dict.get('timestamp', 'N/A')}")

def main():
    st.title("Visual Analytics Engine")
    st.markdown("### Interactive Multi-Dimensional Visualizations & Custom Dashboards")
    st.divider()

    df = get_active_df()
    if df is None:
        st.warning("No dataset found. Please upload or load a sample dataset on the **Upload** page first.")
        st.info("Navigate to the main page from the left sidebar to ingest a dataset.")
        return
        
    if st.session_state.get("charts") is None:
        with st.spinner("Generating automated diagnostic visualizations..."):
            st.session_state["charts"] = generate_auto_charts(df)
            
    if "dashboards" not in st.session_state:
        st.session_state["dashboards"] = {}

    charts = st.session_state["charts"]
    
    # 1. Analytics Metric Overview
    st.header("1. Analytics Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Visualizations", len(charts))
    c2.metric("Custom User Charts", len([c for c in charts if c.get('created_by') == 'user']))
    c3.metric("AI-Derived Charts", len([c for c in charts if c.get('created_by') == 'ai']))
    c4.metric("Saved Dashboards", len(st.session_state["dashboards"]))
    st.divider()

    tab_auto, tab_custom, tab_ai, tab_saved, tab_dash = st.tabs([
        "Auto Charts", "Custom Chart Studio", "AI Chart Studio", "Chart Gallery", "Dashboard Studio"
    ])
    
    # 2. Auto Charts
    with tab_auto:
        st.subheader("Auto-Generated Visualizations")
        auto_c = [c for c in charts if c.get('created_by') == 'system']
        if not auto_c:
            st.info("No auto-generated charts available.")
        else:
            cols = st.columns(2)
            for i, ch in enumerate(auto_c):
                with cols[i % 2]:
                    display_chart_card(ch, f"auto_chart_{i}")
                    
    # 3. Custom Chart Builder
    with tab_custom:
        st.subheader("Custom Chart Studio")
        with st.form("custom_chart_form"):
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                ctype = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie", "Histogram", "Box Plot", "Area", "Heatmap", "Treemap", "Sunburst"])
                agg = st.selectbox("Aggregation Function", ["None", "SUM", "AVG", "COUNT", "MIN", "MAX", "MEDIAN"])
            with cc2:
                x_ax = st.selectbox("X Axis (Primary Dimension)", df.columns)
                num_and_empty = [""] + df.columns.tolist()
                y_ax = st.selectbox("Y Axis (Measure - Optional for Histogram/Pie)", num_and_empty)
            with cc3:
                title_in = st.text_input("Chart Title", placeholder="e.g. Revenue by Region")
                color_by = st.selectbox("Group / Color By (Optional)", ["None"] + df.columns.tolist())
                
            submitted = st.form_submit_button("Generate & Save Chart", type="primary")
            if submitted:
                try:
                    y_ax_val = y_ax if y_ax else None
                    fig = create_custom_chart(df, ctype, x_ax, y_ax_val, agg, color_by)
                    final_title = title_in if title_in else f"{ctype} of {y_ax_val or x_ax}"
                    import uuid, datetime
                    st.session_state["charts"].append({
                        "id": str(uuid.uuid4()),
                        "title": final_title,
                        "fig": fig,
                        "type": ctype,
                        "created_by": "user",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.success(f"Chart '{final_title}' saved to gallery!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating chart: {str(e)}")

    # 4. AI Chart Builder
    with tab_ai:
        st.subheader("Natural Language Chart Studio")
        st.write("Describe the visualization you want to generate (e.g. *'Show monthly revenue trend'* or *'Compare cost across products'*).")
        with st.form("ai_chart_form"):
            ai_request = st.text_input("Visualization Request", placeholder="e.g. Distribution of units sold by category")
            ai_submitted = st.form_submit_button("Generate Visual", type="primary")
            
            if ai_submitted:
                if not ai_request:
                    st.error("Please enter a visual request.")
                else:
                    try:
                        ai_ch = create_ai_chart(df, ai_request)
                        st.session_state["charts"].append(ai_ch)
                        st.success(f"Successfully created: **{ai_ch['title']}**")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create chart: {str(e)}")

    # 5. Chart Gallery
    with tab_saved:
        st.subheader("Chart Gallery & Inventory")
        if not charts:
            st.info("No charts in the gallery.")
        else:
            del_col1, del_col2 = st.columns([3, 1])
            with del_col1:
                chart_to_del = st.selectbox("Select Chart to Delete", [f"{c['title']} ({c.get('type')})" for c in charts])
            with del_col2:
                st.write("")
                st.write("")
                if st.button("Delete Selected Chart", type="secondary"):
                    title_target = chart_to_del.split(" (")[0]
                    st.session_state["charts"] = [c for c in charts if c['title'] != title_target]
                    st.success("Deleted!")
                    st.rerun()
                    
            st.divider()
            gal_cols = st.columns(2)
            for i, ch in enumerate(charts):
                with gal_cols[i % 2]:
                    display_chart_card(ch, f"gallery_chart_{i}")

    # 6. Dashboard Studio
    with tab_dash:
        st.subheader("Dashboard Builder")
        st.write("Group multiple visual cards into named dashboard views.")
        
        with st.form("dash_builder"):
            dash_name = st.text_input("Dashboard Name", placeholder="e.g. Executive Performance View")
            chart_titles = [c['title'] for c in charts]
            selected_chart_names = st.multiselect("Select Charts to Include", chart_titles)
            save_dash = st.form_submit_button("Save Dashboard", type="primary")
            
            if save_dash:
                if not dash_name or not selected_chart_names:
                    st.error("Please provide a dashboard name and select at least one chart.")
                else:
                    st.session_state["dashboards"][dash_name] = selected_chart_names
                    st.success(f"Dashboard '{dash_name}' saved!")
                    st.rerun()
                    
        if st.session_state["dashboards"]:
            st.divider()
            st.subheader("Saved Dashboards")
            view_dash = st.selectbox("Select Dashboard to View", list(st.session_state["dashboards"].keys()))
            if view_dash:
                st.markdown(f"### 🗂️ {view_dash}")
                dash_charts = [c for c in charts if c['title'] in st.session_state["dashboards"][view_dash]]
                d_cols = st.columns(2)
                for i, dch in enumerate(dash_charts):
                    with d_cols[i % 2]:
                        display_chart_card(dch, f"dash_chart_{i}")

if __name__ == "__main__":
    main()
