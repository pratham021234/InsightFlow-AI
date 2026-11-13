import streamlit as st
import datetime
from services.report_generator import (
    build_report_data,
    generate_html_report,
    generate_pdf_report,
    generate_docx_report
)
from utils.session_manager import get_active_df
from services.kpi_engine import generate_default_kpis
from services.insights_engine import (
    generate_executive_summary, generate_key_findings,
    identify_risks, identify_opportunities, generate_recommendations
)
from services.visualization_engine import generate_auto_charts

st.set_page_config(page_title="Reports & Exports", page_icon="📄", layout="wide")

def main():
    st.title("Analytics Report Export System")
    st.markdown("### Generate Professional Multi-Format Executive Reports")
    st.divider()

    df = get_active_df()
    if df is None:
        st.warning("No dataset found. Please upload or load a sample dataset on the **Upload** page first.")
        st.info("Navigate to the main page from the left sidebar to ingest a dataset.")
        return

    dataset_type = st.session_state.get("dataset_type", "General Dataset")

    # Auto-compile prerequisites if user came directly to Reports page
    if st.session_state.get("kpis") is None:
        st.session_state["kpis"] = generate_default_kpis(df, dataset_type)
    if st.session_state.get("charts") is None:
        st.session_state["charts"] = generate_auto_charts(df)
    if st.session_state.get("executive_summary") is None:
        st.session_state["executive_summary"] = generate_executive_summary(df, dataset_type, st.session_state["kpis"])
        st.session_state["insights_findings"] = generate_key_findings(df, dataset_type)
        st.session_state["insights_risks"] = identify_risks(dataset_type, df)
        st.session_state["insights_opps"] = identify_opportunities(dataset_type, df)
        st.session_state["insights_recs"] = generate_recommendations(dataset_type, df)

    if "reports" not in st.session_state:
        st.session_state["reports"] = []

    # 1. Report Dashboard Layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("1. Report Customization")
        with st.form("branding_form"):
            st.markdown("**Executive Branding**")
            title = st.text_input("Report Title", value="Executive Analytics Summary")
            company = st.text_input("Company / Organization", value="InsightFlow Client")
            analyst = st.text_input("Lead Analyst", value="InsightFlow Analytics")
            
            st.markdown("**Sections to Include**")
            inc_prof = st.checkbox("Include Profiling Summary", value=True)
            inc_clean = st.checkbox("Include Data Cleaning Logs", value=False)
            inc_kpi = st.checkbox("Include Key Performance Indicators (KPIs)", value=True)
            inc_chart = st.checkbox("Include Visualizations (HTML)", value=True)
            inc_ins = st.checkbox("Include Strategic Observations & Risks", value=True)
            inc_chat = st.checkbox("Include Chat Analysis Transcript", value=False)
            
            build_btn = st.form_submit_button("Compile Report Draft", type="primary")

        if build_btn:
            selections = {
                "profiling": inc_prof,
                "cleaning": inc_clean,
                "kpis": inc_kpi,
                "charts": inc_chart,
                "insights": inc_ins,
                "chat": inc_chat
            }
            branding = {
                "title": title,
                "company": company,
                "analyst": analyst
            }
            st.session_state["report_draft_data"] = build_report_data(st.session_state, selections)
            st.session_state["report_draft_brand"] = branding
            st.success("Draft Compiled! Choose an export format on the right to download.")
            
    with col2:
        st.subheader("2. Export Center")
        if "report_draft_data" in st.session_state and st.session_state["report_draft_data"]:
            brand = st.session_state["report_draft_brand"]
            r_data = st.session_state["report_draft_data"]
            
            st.success(f"**Document Draft Ready:** `{brand['title']}` for **{brand['company']}**")
            st.caption(f"Domain Profile: **{r_data.get('dataset_type', 'General')}** | Records: **{r_data.get('rows', len(df))}**")
            
            st.markdown("### Select Output Format to Download")
            
            d1, d2, d3 = st.columns(3)
            
            # HTML
            with d1:
                html_str = generate_html_report(r_data, brand)
                st.download_button(
                    label="Download HTML 🌐",
                    data=html_str,
                    file_name=f"{brand['company'].lower().replace(' ', '_')}_report.html",
                    mime="text/html",
                    use_container_width=True
                )
                st.caption("Standalone interactive report with embedded charts and CSS.")
                
            # PDF
            with d2:
                try:
                    pdf_buffer = generate_pdf_report(r_data, brand)
                    st.download_button(
                        label="Download PDF 📄",
                        data=pdf_buffer.getvalue(),
                        file_name=f"{brand['company'].lower().replace(' ', '_')}_report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.caption("Print-ready PDF report generated via ReportLab.")
                except Exception as e:
                    st.error(f"PDF generation error: {str(e)}")
                    st.button("Download PDF 📄", disabled=True, use_container_width=True)
                    
            # DOCX
            with d3:
                try:
                    docx_buffer = generate_docx_report(r_data, brand)
                    st.download_button(
                        label="Download DOCX 📝",
                        data=docx_buffer.getvalue(),
                        file_name=f"{brand['company'].lower().replace(' ', '_')}_report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                    st.caption("Fully editable Microsoft Word document.")
                except Exception as e:
                    st.error(f"DOCX generation error: {str(e)}")
                    st.button("Download DOCX 📝", disabled=True, use_container_width=True)
                    
            st.divider()
            with st.expander("Preview Draft Contents", expanded=True):
                if r_data.get("executive_summary"):
                    st.markdown("**Executive Summary:**")
                    st.write(r_data["executive_summary"])
                if r_data.get("kpis"):
                    st.markdown(f"**KPIs Compiled:** `{len(r_data['kpis'])} metrics`")
                if r_data.get("insights"):
                    st.markdown(f"**Strategic Observations:** `{len(r_data['insights'])} items`")
                if r_data.get("charts"):
                    st.markdown(f"**Visualizations Included:** `{len(r_data['charts'])} charts`")
        else:
            st.info("Fill out the customization parameters on the left and click **Compile Report Draft** to unlock document downloads.")

if __name__ == "__main__":
    main()
