import streamlit as st
import datetime
from services.report_generator import (
    build_report_data,
    generate_html_report,
    generate_pdf_report,
    generate_docx_report
)

st.set_page_config(page_title="Reports & Exports", page_icon="📄", layout="wide")

def main():
    st.title("Analytics Report Export System")
    st.markdown("### Generate Executive Quality Reports")
    st.divider()

    # Verify if prerequisites exist
    if "executive_summary" not in st.session_state and "kpis" not in st.session_state:
        st.warning("No analytic data found to compile. Please upload a dataset and run the AI Insights or KPI engine first.")
        st.stop()

    if "reports" not in st.session_state:
        st.session_state["reports"] = []

    # 1. Report Dashboard Layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("1. Report Customization")
        with st.form("branding_form"):
            st.markdown("**Branding**")
            title = st.text_input("Report Title", value="Executive Analytics Summary")
            company = st.text_input("Company Name", value="ACME Corp")
            analyst = st.text_input("Analyst Name", value="InsightFlow AI User")
            
            st.markdown("**Include Sections**")
            inc_prof = st.checkbox("Include Profiling", value=True)
            inc_clean = st.checkbox("Include Cleaning Logs", value=False)
            inc_kpi = st.checkbox("Include KPIs", value=True)
            inc_chart = st.checkbox("Include Charts (HTML only)", value=True)
            inc_ins = st.checkbox("Include AI Insights", value=True)
            inc_chat = st.checkbox("Include Chat Analysis", value=False)
            
            build_btn = st.form_submit_button("Compile Draft", type="primary")

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
            st.success("Draft Compiled! Review and Download in the adjacent panel.")
            
    with col2:
        st.subheader("2. Export Center")
        if "report_draft_data" in st.session_state:
            brand = st.session_state["report_draft_brand"]
            r_data = st.session_state["report_draft_data"]
            
            st.info(f"**Ready to Export:** {brand['title']} for {brand['company']}")
            
            st.markdown("### Select Format to Download")
            
            d1, d2, d3 = st.columns(3)
            
            # HTML
            with d1:
                html_str = generate_html_report(r_data, brand)
                st.download_button(
                    label="Download HTML 🌐",
                    data=html_str,
                    file_name="InsightFlow_Report.html",
                    mime="text/html",
                    use_container_width=True
                )
                
            # PDF
            with d2:
                try:
                    pdf_buffer = generate_pdf_report(r_data, brand)
                    st.download_button(
                        label="Download PDF 📄",
                        data=pdf_buffer,
                        file_name="InsightFlow_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(str(e))
                    st.button("Download PDF 📄", disabled=True, use_container_width=True)
                    
            # DOCX
            with d3:
                try:
                    docx_buffer = generate_docx_report(r_data, brand)
                    st.download_button(
                        label="Download DOCX 📝",
                        data=docx_buffer,
                        file_name="InsightFlow_Report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(str(e))
                    st.button("Download DOCX 📝", disabled=True, use_container_width=True)
                    
            st.divider()
            with st.expander("Preview Text Content"):
                if r_data.get("executive_summary"):
                    st.write("**Executive Summary:**")
                    st.write(r_data["executive_summary"])
                if r_data.get("kpis"):
                    st.write("**KPIs Compiled:**", len(r_data["kpis"]))
                if r_data.get("insights"):
                    st.write("**Findings Compiled:**", len(r_data["insights"]))
        else:
            st.write("Compile a draft using the form on the left to unlock downloads.")

if __name__ == "__main__":
    main()
