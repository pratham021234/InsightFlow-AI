import streamlit as st
import pandas as pd
import io
from datetime import datetime
from services.cleaner import (
    detect_missing_values, fill_missing_values,
    detect_duplicates, remove_duplicates,
    detect_outliers, remove_outliers, cap_outliers,
    detect_dtype_issues, convert_dtype,
    rename_columns, drop_columns, generate_cleaning_summary
)

st.set_page_config(page_title="Data Cleaning Engine", page_icon="🧹", layout="wide")

def log_operation(operation: str, rows_affected: str, cols_affected: str):
    st.session_state["cleaning_log"].append({
        "Operation": operation,
        "Affected Rows": rows_affected,
        "Affected Columns": cols_affected,
        "Timestamp": datetime.now().strftime("%I:%M %p")
    })

def main():
    st.title("Interactive Data Cleaning Engine")
    st.markdown("### Detect, review, and clean data quality issues seamlessly")
    
    if "original_df" not in st.session_state or st.session_state["original_df"] is None:
        st.warning("No dataset found. Please upload a dataset first.")
        return
        
    if "cleaned_df" not in st.session_state:
        st.session_state["cleaned_df"] = st.session_state["original_df"].copy()
        
    if "cleaning_log" not in st.session_state:
        st.session_state["cleaning_log"] = []
        
    original_df = st.session_state["original_df"]
    df = st.session_state["cleaned_df"]
    
    # 1. Cleaning Dashboard
    st.header("1. Cleaning Dashboard Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Rows Before", f"{len(original_df):,}")
    col2.metric("Rows After", f"{len(df):,}")
    col3.metric("Columns", f"{len(df.columns):,}")
    col4.metric("Missing Values Remaining", f"{df.isna().sum().sum():,}")
    col5.metric("Duplicates Remaining", f"{df.duplicated().sum():,}")
    st.divider()

    # 2. Missing Value Cleaning
    st.header("2. Missing Value Cleaning")
    missing_issues = detect_missing_values(df)
    if not missing_issues:
        st.success("No missing values found!")
    else:
        st.dataframe(pd.DataFrame(missing_issues)[["Column Name", "Missing Count", "Missing Percentage", "Suggested Fix"]], use_container_width=True)
        for issue in missing_issues:
            col_name = issue["Column Name"]
            with st.expander(f"Clean Column: {col_name} (Suggested: {issue['Suggested Fix']})"):
                action = st.selectbox(
                    f"Action for {col_name}",
                    ["Ignore", "Fill Mean", "Fill Median", "Fill Mode", "Forward Fill", "Backward Fill", "Remove Rows"],
                    key=f"miss_{col_name}"
                )
                if st.button(f"Apply Missing Value Fix", key=f"btn_miss_{col_name}") and action != "Ignore":
                    st.session_state["cleaned_df"] = fill_missing_values(df, col_name, action)
                    log_operation(f"Missing Values: {action} on {col_name}", "Varies", col_name)
                    st.success(f"Applied {action} to {col_name}!")
                    st.rerun()
    st.divider()

    # 3. Duplicate Cleaning
    st.header("3. Duplicate Cleaning")
    duplicates = detect_duplicates(df)
    st.write(f"**Duplicate Rows Found:** {duplicates}")
    if duplicates > 0:
        if st.button("Remove Duplicates"):
            st.session_state["cleaned_df"] = remove_duplicates(df)
            log_operation("Removed Duplicates", f"{duplicates} Rows", "All Columns")
            st.success("Duplicates removed!")
            st.rerun()
    else:
        st.success("No duplicates found!")
    st.divider()

    # 4. Outlier Detection
    st.header("4. Outlier Detection (IQR Method)")
    outliers = detect_outliers(df)
    if not outliers:
        st.success("No outliers found based on the IQR method!")
    else:
        st.dataframe(pd.DataFrame(outliers)[["Column Name", "Outlier Count", "Outlier Percentage"]], use_container_width=True)
        for out in outliers:
            col_name = out["Column Name"]
            with st.expander(f"Clean Outliers: {col_name} ({out['Outlier Count']} found)"):
                action = st.selectbox(
                    f"Action for {col_name}",
                    ["Ignore", "Cap Outliers", "Remove Outliers"],
                    key=f"out_{col_name}"
                )
                if st.button(f"Apply Outlier Fix", key=f"btn_out_{col_name}") and action != "Ignore":
                    if action == "Cap Outliers":
                        st.session_state["cleaned_df"] = cap_outliers(df, col_name, out['Lower Bound'], out['Upper Bound'])
                        log_operation(f"Capped Outliers on {col_name}", str(out['Outlier Count']), col_name)
                    elif action == "Remove Outliers":
                        st.session_state["cleaned_df"] = remove_outliers(df, col_name, out['Lower Bound'], out['Upper Bound'])
                        log_operation(f"Removed Outliers on {col_name}", str(out['Outlier Count']), col_name)
                    st.success(f"Applied {action} to {col_name}!")
                    st.rerun()
    st.divider()

    # 5. Data Type Corrections
    st.header("5. Data Type Corrections")
    dtypes_issues = detect_dtype_issues(df)
    if not dtypes_issues:
        st.success("No obvious data type issues detected!")
    else:
        for iss in dtypes_issues:
            col_name = iss["Column Name"]
            with st.expander(f"Fix Type: {col_name} - {iss['Issue']}"):
                action = st.selectbox(
                    f"Action for {col_name}",
                    ["Ignore", "Convert to Numeric", "Convert to Datetime", "Convert to Category"],
                    index=["Ignore", "Convert to Numeric", "Convert to Datetime", "Convert to Category"].index(iss['Suggestion']) if iss['Suggestion'] in ["Convert to Numeric", "Convert to Datetime", "Convert to Category"] else 0,
                    key=f"type_{col_name}"
                )
                if st.button(f"Apply Conversion", key=f"btn_type_{col_name}") and action != "Ignore":
                    st.session_state["cleaned_df"] = convert_dtype(df, col_name, action)
                    log_operation(f"Type Conversion: {action} on {col_name}", "All Rows", col_name)
                    st.success("Applied Conversion!")
                    st.rerun()
    st.divider()

    # 6. Column Operations
    st.header("6. Column Operations")
    col_op1, col_op2 = st.columns(2)
    with col_op1:
        st.subheader("Rename Column")
        col_to_rename = st.selectbox("Select column to rename", df.columns, key="rename_select")
        new_name = st.text_input("New Name")
        if st.button("Rename Column"):
            if new_name:
                st.session_state["cleaned_df"] = rename_columns(df, {col_to_rename: new_name})
                log_operation(f"Renamed Column: {col_to_rename} to {new_name}", "All Rows", new_name)
                st.success("Renamed!")
                st.rerun()
    with col_op2:
        st.subheader("Drop Columns")
        cols_to_drop = st.multiselect("Select columns to drop", df.columns, key="drop_select")
        if st.button("Drop Selected Columns"):
            if cols_to_drop:
                st.session_state["cleaned_df"] = drop_columns(df, cols_to_drop)
                log_operation(f"Dropped Columns", "All Rows", ", ".join(cols_to_drop))
                st.success("Dropped!")
                st.rerun()
    st.divider()

    # 7. Cleaning Summary
    st.header("7. Cleaning Summary")
    summary_df = generate_cleaning_summary(st.session_state["cleaning_log"])
    st.dataframe(summary_df, use_container_width=True)
    st.divider()

    # 8. Cleaned Dataset Preview
    st.header("8. Cleaned Dataset Preview")
    st.dataframe(df.head(20), use_container_width=True)
    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.metric("Current Rows", f"{len(df):,}")
    col_p2.metric("Current Columns", f"{len(df.columns):,}")
    col_p3.metric("Current Memory Usage", f"{df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")
    st.divider()

    # 9. Download Cleaned Dataset
    st.header("9. Download Cleaned Dataset")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Cleaned CSV",
            data=csv_buffer.getvalue(),
            file_name="cleaned_dataset.csv",
            mime="text/csv"
        )
    with col_d2:
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        st.download_button(
            label="Download Cleaned Excel",
            data=excel_buffer.getvalue(),
            file_name="cleaned_dataset.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    st.divider()

    # 10. Finalize Cleaning
    st.header("10. Finalize Cleaning")
    st.write("Clicking finalize will formally save the current `cleaned_df` and log state for future modules.")
    if st.button("Finalize Cleaning", type="primary"):
        st.session_state["cleaning_summary"] = summary_df
        st.success("Cleaning finalized! Future modules will now default to using `cleaned_df`.")
        
if __name__ == "__main__":
    main()
