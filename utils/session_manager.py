import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

def init_session_state() -> None:
    """Initialize required keys in Streamlit session state."""
    defaults = {
        "original_df": None,
        "cleaned_df": None,
        "metadata": None,
        "dataset_metadata": None,
        "upload_timestamp": None,
        "upload_logs": [],
        "cleaning_log": [],
        "cleaning_summary": None,
        "dataset_type": "General Dataset",
        "dataset_confidence": 0.0,
        "dataset_entities": [],
        "dataset_description": "",
        "recommended_kpis": [],
        "recommended_charts": [],
        "kpis": None,
        "charts": None,
        "dashboards": {},
        "chat_history": [],
        "executive_summary": None,
        "insights_findings": None,
        "insights_trends": None,
        "insights_anomalies": None,
        "insights_risks": None,
        "insights_opps": None,
        "insights_recs": None,
        "insights_kpi_interp": None,
        "report_draft_data": None,
        "report_draft_brand": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def store_dataset(df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
    """
    Store the uploaded dataset and metadata in session state,
    and reset downstream caches to prevent cross-dataset contamination.
    """
    init_session_state()
    st.session_state["original_df"] = df.copy()
    st.session_state["cleaned_df"] = df.copy()
    st.session_state["metadata"] = metadata
    st.session_state["dataset_metadata"] = metadata
    st.session_state["upload_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Reset downstream module caches
    st.session_state["cleaning_log"] = []
    st.session_state["cleaning_summary"] = None
    st.session_state["kpis"] = None
    st.session_state["charts"] = None
    st.session_state["dashboards"] = {}
    st.session_state["chat_history"] = []
    st.session_state["executive_summary"] = None
    st.session_state["insights_findings"] = None
    st.session_state["insights_trends"] = None
    st.session_state["insights_anomalies"] = None
    st.session_state["insights_risks"] = None
    st.session_state["insights_opps"] = None
    st.session_state["insights_recs"] = None
    st.session_state["insights_kpi_interp"] = None
    st.session_state["report_draft_data"] = None
    st.session_state["report_draft_brand"] = None

    # Run auto domain detection immediately so all pages are informed
    try:
        from services.dataset_detector import (
            detect_dataset_type, generate_dataset_description,
            extract_business_entities, generate_kpi_suggestions,
            generate_chart_suggestions, save_detection_results
        )
        dtype, conf, _ = detect_dataset_type(df)
        desc = generate_dataset_description(dtype)
        ents = extract_business_entities(df, dtype)
        kpi_suggs = generate_kpi_suggestions(dtype)
        chart_suggs = generate_chart_suggestions(dtype)
        save_detection_results(dtype, conf, ents, desc, kpi_suggs, chart_suggs)
    except Exception:
        st.session_state["dataset_type"] = "General Dataset"
        st.session_state["dataset_confidence"] = 0.0

def get_active_df() -> Optional[pd.DataFrame]:
    """Retrieve the active dataframe (cleaned_df if available, else original_df)."""
    if "cleaned_df" in st.session_state and st.session_state["cleaned_df"] is not None:
        return st.session_state["cleaned_df"]
    return st.session_state.get("original_df")

def get_original_df() -> Optional[pd.DataFrame]:
    """Retrieve the original uncleaned dataframe."""
    return st.session_state.get("original_df")

def clear_dataset() -> None:
    """Clear the dataset and all related state from session state."""
    init_session_state()
    keys_to_clear = [
        "original_df", "cleaned_df", "metadata", "dataset_metadata",
        "upload_timestamp", "upload_logs", "cleaning_log", "cleaning_summary",
        "dataset_type", "dataset_confidence", "dataset_entities", "dataset_description",
        "recommended_kpis", "recommended_charts", "kpis", "charts", "dashboards",
        "chat_history", "executive_summary", "insights_findings", "insights_trends",
        "insights_anomalies", "insights_risks", "insights_opps", "insights_recs",
        "insights_kpi_interp", "report_draft_data", "report_draft_brand"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None if not isinstance(st.session_state[key], (list, dict)) else ([] if isinstance(st.session_state[key], list) else {})
