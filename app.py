import streamlit as st
import pandas as pd
import io
from services.data_loader import load_dataset
from utils.session_manager import init_session_state, store_dataset, clear_dataset, get_active_df

# Configuration for professional layout
st.set_page_config(
    page_title="InsightFlow AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
init_session_state()

def _generate_sample_dataset() -> pd.DataFrame:
    """Generate a realistic sample sales dataset for quick evaluation."""
    import numpy as np
    np.random.seed(42)
    n = 120
    dates = pd.date_range(start="2024-01-01", periods=n, freq="D")
    products = np.random.choice(["Enterprise Suite", "Pro Plan", "Starter Kit", "Consulting Hour", "Add-on Module"], size=n, p=[0.25, 0.35, 0.20, 0.10, 0.10])
    regions = np.random.choice(["North America", "Europe", "Asia-Pacific", "Latin America"], size=n, p=[0.4, 0.3, 0.2, 0.1])
    quantities = np.random.randint(1, 15, size=n)
    unit_prices = {"Enterprise Suite": 1200.0, "Pro Plan": 450.0, "Starter Kit": 150.0, "Consulting Hour": 200.0, "Add-on Module": 75.0}
    revenues = [quantities[i] * unit_prices[products[i]] + float(np.random.normal(0, 20)) for i in range(n)]
    costs = [rev * np.random.uniform(0.35, 0.55) for rev in revenues]
    customers = [f"CUST-{np.random.randint(1001, 1050)}" for _ in range(n)]
    
    # Introduce a few realistic missing values and a duplicate to demonstrate cleaning
    df_sample = pd.DataFrame({
        "Order_Date": dates,
        "Customer_ID": customers,
        "Product": products,
        "Region": regions,
        "Quantity": quantities,
        "Revenue": np.round(revenues, 2),
        "Cost": np.round(costs, 2),
        "Status": np.random.choice(["Completed", "Shipped", "Pending"], size=n, p=[0.75, 0.2, 0.05])
    })
    # Add 3 missing values and 2 duplicate rows for testing
    df_sample.loc[5, "Region"] = None
    df_sample.loc[12, "Cost"] = None
    df_sample.loc[25, "Customer_ID"] = None
    dup_rows = df_sample.iloc[[0, 1]].copy()
    df_sample = pd.concat([df_sample, dup_rows], ignore_index=True)
    return df_sample

def main():
    st.title("InsightFlow AI")
    st.markdown("### AI Powered Universal Data Analytics Platform")
    st.caption("Upload raw CSV or Excel datasets to automatically inspect data quality, generate domain KPIs, visualize metrics, and export executive reports.")
    st.divider()

    # 1. Dataset Ingestion / Controls
    st.header("1. Ingest Dataset")
    
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader(
            "Upload Dataset (Supported formats: CSV, XLSX, XLS)",
            type=["csv", "xlsx", "xls"],
            key="file_uploader_widget"
        )
    with col_up2:
        st.write("**Quick Evaluation:**")
        if st.button("Load Sample Sales Dataset", use_container_width=True):
            with st.spinner("Generating sample sales dataset..."):
                sample_df = _generate_sample_dataset()
                sample_bytes = sample_df.to_csv(index=False).encode('utf-8')
                sample_metadata = {
                    "filename": "sample_enterprise_sales.csv",
                    "rows": len(sample_df),
                    "columns": len(sample_df.columns),
                    "memory_usage": f"{sample_df.memory_usage(deep=True).sum() / 1024:.2f} KB",
                    "file_size": f"{len(sample_bytes) / 1024:.2f} KB",
                    "encoding": "utf-8",
                    "file_type": "csv"
                }
                store_dataset(sample_df, sample_metadata)
                st.session_state["upload_logs"] = ["Loaded built-in sample sales dataset with 122 records."]
                st.success("Sample dataset loaded! You can now explore all pages.")
                st.rerun()

    # Handle Uploaded File
    if uploaded_file is not None:
        # Check if already processed this exact file
        current_meta = st.session_state.get("metadata")
        if current_meta is None or current_meta.get("filename") != uploaded_file.name:
            try:
                with st.spinner("Parsing and validating dataset..."):
                    df, metadata, logs = load_dataset(uploaded_file, uploaded_file.name)
                    store_dataset(df, metadata)
                    st.session_state["upload_logs"] = logs
                    st.success(f"Successfully loaded '{uploaded_file.name}'!")
                    st.rerun()
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Unexpected parsing error: {str(e)}")

    # Check Active Dataset
    active_df = get_active_df()
    metadata = st.session_state.get("metadata")

    if active_df is not None and metadata is not None:
        # Dataset Active Action Bar
        col_bar1, col_bar2 = st.columns([3, 1])
        with col_bar1:
            st.success(f"**Active Dataset:** `{metadata['filename']}` ({len(active_df):,} rows, {len(active_df.columns)} columns) | Type: **{st.session_state.get('dataset_type', 'General Dataset')}**")
        with col_bar2:
            if st.button("Clear Active Dataset", type="secondary", use_container_width=True):
                clear_dataset()
                st.info("Active dataset cleared.")
                st.rerun()

        # Render Upload Logs
        if st.session_state.get("upload_logs"):
            with st.expander("Diagnostic Ingestion Logs"):
                for log in st.session_state["upload_logs"]:
                    if "Failed" in log or "Engine" in log and "failed" in log:
                        st.write(f"⚠️ {log}")
                    elif "Successfully" in log or "loaded" in log:
                        st.write(f"✅ {log}")
                    else:
                        st.write(f"ℹ️ {log}")

        st.divider()

        # 2. Dataset Overview Section
        st.header("2. Dataset Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Dataset Name", metadata["filename"])
            st.metric("Encoding Used", metadata.get("encoding", "N/A"))
        with col2:
            st.metric("Total Rows", f"{len(active_df):,}")
            st.metric("File Format", metadata.get("file_type", "csv").upper())
        with col3:
            st.metric("Total Columns", f"{len(active_df.columns):,}")
            st.metric("Detected Domain", st.session_state.get("dataset_type", "General"))
        with col4:
            st.metric("Memory Footprint", metadata.get("memory_usage", "N/A"))
            st.metric("File Size", metadata.get("file_size", "N/A"))

        st.divider()

        # 3. Dataset Preview Section
        st.header("3. Dataset Preview")
        preview_rows = st.slider("Preview Rows:", min_value=5, max_value=50, value=10, step=5)
        st.dataframe(active_df.head(preview_rows), use_container_width=True)

        st.divider()

        # 4. Column Information Section
        st.header("4. Column Information")
        dtypes_data = []
        for col in active_df.columns:
            dtypes_data.append({
                "Column Name": col,
                "Data Type": str(active_df[col].dtype),
                "Non-Null Count": f"{active_df[col].notna().sum():,} / {len(active_df):,}",
                "Null %": f"{(active_df[col].isna().sum() / len(active_df)) * 100:.1f}%",
                "Unique Values": active_df[col].nunique()
            })
        dtypes_df = pd.DataFrame(dtypes_data)
        st.dataframe(dtypes_df, use_container_width=True)
        
        st.divider()
        st.info("👉 **Next Steps:** Use the left navigation sidebar to explore **Dataset Intelligence**, perform **Data Profiling**, execute **Data Cleaning**, monitor **KPIs**, build **Visualizations**, query via **Chat With Data**, or compile **Executive Reports**.")

    else:
        # Friendly empty state
        st.info("No dataset is currently loaded. Please upload a CSV, XLSX, or XLS file above, or click **Load Sample Sales Dataset** to explore the platform immediately.")

if __name__ == "__main__":
    main()
