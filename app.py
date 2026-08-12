import streamlit as st
import pandas as pd
from services.data_loader import load_dataset
from utils.session_manager import init_session_state, store_dataset, clear_dataset

# Configuration for professional layout
st.set_page_config(
    page_title="InsightFlow AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
init_session_state()

def main():
    st.title("InsightFlow AI")
    st.markdown("### AI Powered Universal Data Analytics Platform")
    st.divider()

    # 1. Upload Dataset Section
    st.header("1. Upload Dataset")
    
    uploaded_file = st.file_uploader(
        "Upload Dataset (Supported formats: CSV, XLSX, XLS)",
        type=["csv", "xlsx", "xls"]
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Loading dataset..."):
                df, metadata, logs = load_dataset(uploaded_file, uploaded_file.name)
                store_dataset(df, metadata)
                st.session_state["upload_logs"] = logs
                st.session_state["dataset_metadata"] = metadata
                st.success("Dataset uploaded successfully!")
        except ValueError as e:
            st.error(str(e))
            clear_dataset()
    else:
        st.info("Please upload a dataset.")
        clear_dataset()
        if "upload_logs" in st.session_state:
            del st.session_state["upload_logs"]
        return

    # Render Upload Logs
    if "upload_logs" in st.session_state:
        with st.expander("Diagnostic Upload Logs"):
            for log in st.session_state["upload_logs"]:
                if "Failed" in log:
                    st.write(f"⚠️ {log}")
                elif "Success" in log:
                    st.write(f"✅ {log}")
                else:
                    st.write(f"🔄 {log}")

    # Proceed only if data exists in session state
    if st.session_state["original_df"] is not None:
        df = st.session_state["original_df"]
        metadata = st.session_state["dataset_metadata"]

        st.divider()

        # 2. Dataset Overview Section
        st.header("2. Dataset Overview")
        
        # Professional KPI cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Dataset Name", metadata["filename"])
            st.metric("Encoding Used", metadata["encoding"])
        with col2:
            st.metric("Total Rows", f"{metadata['rows']:,}")
            st.metric("File Format", metadata["file_type"].upper())
        with col3:
            st.metric("Total Columns", f"{metadata['columns']:,}")
        with col4:
            st.metric("Memory Footprint", metadata["memory_usage"])
            st.metric("File Size", metadata["file_size"])

        st.divider()

        # 3. Dataset Preview Section
        st.header("3. Dataset Preview")
        st.dataframe(df.head(10), use_container_width=True)

        st.divider()

        # 4. Column Information Section
        st.header("4. Column Information")
        # Extract dtypes and convert to dataframe
        dtypes_df = pd.DataFrame(df.dtypes, columns=["Data Type"]).reset_index()
        dtypes_df.rename(columns={"index": "Column Name"}, inplace=True)
        dtypes_df["Data Type"] = dtypes_df["Data Type"].astype(str)
        st.dataframe(dtypes_df, use_container_width=True)

if __name__ == "__main__":
    main()
