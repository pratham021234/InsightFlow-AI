import streamlit as st
import pandas as pd
from typing import Dict, Any
from datetime import datetime

def init_session_state() -> None:
    """Initialize required keys in Streamlit session state."""
    if "original_df" not in st.session_state:
        st.session_state["original_df"] = None
    if "metadata" not in st.session_state:
        st.session_state["metadata"] = None
    if "upload_timestamp" not in st.session_state:
        st.session_state["upload_timestamp"] = None

def store_dataset(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """Store the uploaded dataset and metadata in session state."""
    st.session_state["original_df"] = df
    st.session_state["metadata"] = metadata
    st.session_state["upload_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_dataset() -> pd.DataFrame:
    """Retrieve the stored dataframe from session state."""
    return st.session_state.get("original_df")

def clear_dataset() -> None:
    """Clear the dataset from session state."""
    st.session_state["original_df"] = None
    st.session_state["metadata"] = None
    st.session_state["upload_timestamp"] = None
