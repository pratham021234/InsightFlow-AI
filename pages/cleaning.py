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
from utils.session_manager import get_active_df, get_original_df

st.set_page_config(page_title="Data Cleaning Engine", page_icon="🧹", layout="wide")

def log_operation(operation: str, rows_affected: str, cols_affected: str):
    if "cleaning_log" not in st.session_state:
        st.session_state["cleaning_log"] = []
    st.session_state["cleaning_log"].append({
        "Operation": operation,
        "Affected Rows": rows_affected,
        "Affected Columns": cols_affected,
        "Timestamp": datetime.now().strftime("%I:%M:%S %p")
    })

def main():
    st.title("Interactive Data Cleaning Engine")
    st.markdown("### Detect, Review, and Remediate Data Quality Issues Seamlessly")
    st.divider()
    
    original_df = get_original_df()
    if original_df is None:
        st.warning("No dataset found. Please upload or load a sample dataset on the **Upload** page first.")
        st.info("Navigate to the main page from the left sidebar to ingest a dataset.")
        return
        
    if "cleaned_df" not in st.session_state or st.session_state["cleaned_df"] is None:
        st.session_state["cleaned_df"] = original_df.copy()
        
    if "cleaning_log" not in st.session_state:
        st.session_state["cleaning_log"] = []
        
    df = st.session_state["cleaned_df"]
    
    # Reset / Undo controls bar
    bar1, bar2 = st.columns([3, 1])
    with bar1:
        st.caption(f"Working with active dataset. Changes will update the active state used by other modules.")
    with bar2:
        if st.button("Reset to Original Dataset", type="secondary", use_container_width=True):
            st.session_state["cleaned_df"] = original_df.copy()
            st.session_state["cleaning_log"] = []
            st.session_state["cleaning_summary"] = None
            st.success("Cleaned dataset reset to original uncleaned version!")
            st.rerun()

    # 1. Cleaning Dashboard Overview
    st.header("1. Cleaning Audit Dashboard")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Rows Before", f"{len(original_df):,}")
    col2.metric("Rows After", f"{len(df):,}", delta=f"{len(df) - len(original_df)} rows")
    col3.metric("Columns", f"{len(df.columns):,}")
    col4.metric("Missing Values", f"{df.isna().sum().sum():,}", delta_color="inverse")
    col5.metric("Duplicates", f"{df.duplicated().sum():,}", delta_color="inverse")
    st.divider()

    # 2. Missing Value Cleaning
    st.header("2. Missing Value Imputation")
    missing_issues = detect_missing_values(df)
    if not missing_issues:
        st.success("No missing values found across any columns!")
    else:
        st.dataframe(pd.DataFrame(missing_issues)[["Column Name", "Missing Count", "Missing Percentage", "Suggested Fix"]], use_container_width=True)
        for issue in missing_issues:
            col_name = issue["Column Name"]
            col_type = issue["Data Type"]
            is_num = pd.api.types.is_numeric_dtype(df[col_name])
            
            # Select appropriate strategy list based on data type
            if is_num:
                strategies = ["Ignore", "Fill Median", "Fill Mean", "Fill Mode", "Forward Fill", "Backward Fill", "Remove Rows"]
            else:
                strategies = ["Ignore", "Fill Mode", "Forward Fill", "Backward Fill", "Remove Rows"]
                
            default_strat_idx = strategies.index(issue["Suggested Fix"]) if issue["Suggested Fix"] in strategies else 0

            with st.expander(f"Clean Column: `{col_name}` ({issue['Missing Count']} missing - Suggested: {issue['Suggested Fix']})"):
                action = st.selectbox(
                    f"Choose Strategy for '{col_name}'",
                    strategies,
                    index=default_strat_idx,
                    key=f"miss_{col_name}"
                )
                if st.button(f"Apply Fix to {col_name}", key=f"btn_miss_{col_name}") and action != "Ignore":
                    st.session_state["cleaned_df"] = fill_missing_values(df, col_name, action)
                    log_operation(f"Missing Values: {action} on {col_name}", f"{issue['Missing Count']} Nulls", col_name)
                    st.success(f"Successfully applied {action} to '{col_name}'!")
                    st.rerun()
    st.divider()

    # 3. Duplicate Cleaning
    st.header("3. Duplicate Row Deduplication")
    duplicates = detect_duplicates(df)
    col_dup1, col_dup2 = st.columns([2, 1])
    with col_dup1:
        st.write(f"**Duplicate Records Detected:** `{duplicates}` ({(duplicates/len(df)*100 if len(df) > 0 else 0):.2f}% of dataset)")
    with col_dup2:
        if duplicates > 0:
            if st.button("Remove Duplicate Rows", type="primary", use_container_width=True):
                st.session_state["cleaned_df"] = remove_duplicates(df)
                log_operation("Removed Duplicates", f"{duplicates} Rows", "All Columns")
                st.success(f"Removed {duplicates} duplicate rows!")
                st.rerun()
        else:
            st.success("No duplicate records found.")
    st.divider()

    # 4. Outlier Detection (IQR Method)
    st.header("4. Outlier Detection & Treatment (1.5 × IQR Method)")
    outliers = detect_outliers(df)
    if not outliers:
        st.success("No statistical outliers detected based on the 1.5 × IQR standard.")
    else:
        st.dataframe(pd.DataFrame(outliers)[["Column Name", "Outlier Count", "Outlier Percentage", "Lower Bound", "Upper Bound"]], use_container_width=True)
        for out in outliers:
            col_name = out["Column Name"]
            with st.expander(f"Treat Outliers in `{col_name}` ({out['Outlier Count']} outliers detected)"):
                action = st.selectbox(
                    f"Outlier Treatment for '{col_name}'",
                    ["Ignore", "Cap Outliers (Winsorize to Bounds)", "Remove Outliers"],
                    key=f"out_{col_name}"
                )
                if st.button(f"Apply Outlier Fix to {col_name}", key=f"btn_out_{col_name}") and action != "Ignore":
                    if "Cap" in action:
                        st.session_state["cleaned_df"] = cap_outliers(df, col_name, out['Lower Bound'], out['Upper Bound'])
                        log_operation(f"Capped Outliers on {col_name}", str(out['Outlier Count']), col_name)
                    elif "Remove" in action:
                        st.session_state["cleaned_df"] = remove_outliers(df, col_name, out['Lower Bound'], out['Upper Bound'])
                        log_operation(f"Removed Outliers on {col_name}", str(out['Outlier Count']), col_name)
                    st.success(f"Applied {action} on '{col_name}'!")
                    st.rerun()
    st.divider()

    # 5. Data Type Corrections
    st.header("5. Data Type Corrections & Optimization")
    dtypes_issues = detect_dtype_issues(df)
    if not dtypes_issues:
        st.success("No obvious data type anomalies or suboptimal encodings detected.")
    else:
        for iss in dtypes_issues:
            col_name = iss["Column Name"]
            with st.expander(f"Correct Type: `{col_name}` — {iss['Issue']}"):
                action = st.selectbox(
                    f"Conversion Target for '{col_name}'",
                    ["Ignore", "Convert to Numeric", "Convert to Datetime", "Convert to Category"],
                    index=["Ignore", "Convert to Numeric", "Convert to Datetime", "Convert to Category"].index(iss['Suggestion']) if iss['Suggestion'] in ["Convert to Numeric", "Convert to Datetime", "Convert to Category"] else 0,
                    key=f"type_{col_name}"
                )
                if st.button(f"Apply Conversion to {col_name}", key=f"btn_type_{col_name}") and action != "Ignore":
                    st.session_state["cleaned_df"] = convert_dtype(df, col_name, action)
                    log_operation(f"Type Conversion: {action} on {col_name}", "All Rows", col_name)
                    st.success(f"Successfully converted '{col_name}'!")
                    st.rerun()
    st.divider()

    # 6. Column Renaming & Dropping
    st.header("6. Column Schema Operations")
    col_op1, col_op2 = st.columns(2)
    with col_op1:
        st.subheader("Rename Column")
        col_to_rename = st.selectbox("Select column to rename", df.columns, key="rename_select")
        new_name = st.text_input("New Column Name", key="rename_input")
        if st.button("Apply Column Rename"):
            if new_name and new_name != col_to_rename:
                st.session_state["cleaned_df"] = rename_columns(df, {col_to_rename: new_name})
                log_operation(f"Renamed Column", "All Rows", f"{col_to_rename} -> {new_name}")
                st.success(f"Renamed '{col_to_rename}' to '{new_name}'!")
                st.rerun()
    with col_op2:
        st.subheader("Drop Columns")
        cols_to_drop = st.multiselect("Select columns to drop", df.columns, key="drop_select")
        if st.button("Drop Selected Columns", type="secondary"):
            if cols_to_drop:
                st.session_state["cleaned_df"] = drop_columns(df, cols_to_drop)
                log_operation("Dropped Columns", "All Rows", ", ".join(cols_to_drop))
                st.success(f"Dropped {len(cols_to_drop)} columns!")
                st.rerun()
    st.divider()

    # 7. Cleaning Audit Trail
    st.header("7. Cleaning Operation Audit Trail")
    summary_df = generate_cleaning_summary(st.session_state["cleaning_log"])
    if not summary_df.empty:
        st.dataframe(summary_df, use_container_width=True)
    else:
        st.info("No cleaning operations have been performed yet.")
    st.divider()

    # 8. Cleaned Dataset Preview & Download
    st.header("8. Export Cleaned Dataset")
    st.dataframe(df.head(15), use_container_width=True)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Cleaned CSV",
            data=csv_buffer.getvalue(),
            file_name="cleaned_dataset.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_d2:
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        st.download_button(
            label="Download Cleaned Excel (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name="cleaned_dataset.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
