import streamlit as st
import pandas as pd
from services.dataset_detector import (
    detect_dataset_type,
    generate_dataset_description,
    extract_business_entities,
    generate_kpi_suggestions,
    generate_chart_suggestions,
    save_detection_results
)

st.set_page_config(page_title="Dataset Intelligence", page_icon="🧠", layout="wide")

def main():
    st.title("Dataset Intelligence")
    st.markdown("### Smart Detection and Business Context Engine")
    st.divider()

    # Priority to cleaned_df, fallback to original_df
    df = None
    if "cleaned_df" in st.session_state and st.session_state["cleaned_df"] is not None:
        df = st.session_state["cleaned_df"]
    elif "original_df" in st.session_state and st.session_state["original_df"] is not None:
        df = st.session_state["original_df"]

    if df is None:
        st.warning("No dataset found. Please upload a dataset on the Upload page first.")
        return

    with st.spinner("Analyzing dataset intelligence..."):
        # Detect type
        dataset_type, confidence, all_scores = detect_dataset_type(df)
        
        # Format Domain name
        domain_name = dataset_type if dataset_type == "General Dataset" else f"{dataset_type} Dataset"
        
        # Generate metadata
        description = generate_dataset_description(dataset_type)
        entities = extract_business_entities(df, dataset_type)
        kpis = generate_kpi_suggestions(dataset_type)
        charts = generate_chart_suggestions(dataset_type)
        
        # Save to state
        save_detection_results(dataset_type, confidence, entities, description, kpis, charts)

    # 1. Detection Summary
    st.header("1. Detection Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Detected Dataset Type:**\n\n### {domain_name}")
    with col2:
        st.success(f"**Confidence Score:**\n\n### {confidence:.1f}%")
        
    st.divider()

    # 2. Confidence Scores
    st.header("2. Domain Confidence Scores")
    if all_scores:
        score_df = pd.DataFrame(list(all_scores.items()), columns=["Domain", "Confidence (%)"])
        score_df = score_df.sort_values(by="Confidence (%)", ascending=False).head(5)
        st.dataframe(score_df, use_container_width=True)
    else:
        st.write("No distinct domain signatures found.")
        
    st.divider()

    # 3. Business Description
    st.header("3. Business Description")
    st.markdown(f"> {description}")
    
    st.divider()

    # 4. Business Entities
    st.header("4. Detected Business Entities")
    if entities:
        cols = st.columns(min(len(entities), 6))
        for i, entity in enumerate(entities[:6]):
            cols[i].button(entity, disabled=True, key=f"entity_{i}")
    else:
        st.write("No specific business entities detected.")

    st.divider()

    # 5. KPI Recommendations
    st.header("5. KPI Recommendations")
    st.markdown("These KPIs will be automatically generated in Module 5:")
    kpi_cols = st.columns(3)
    for i, kpi in enumerate(kpis):
        kpi_cols[i % 3].markdown(f"- **{kpi}**")

    st.divider()

    # 6. Visualization Recommendations
    st.header("6. Visualization Recommendations")
    st.markdown("Recommended charts based on the detected domain:")
    chart_cols = st.columns(3)
    for i, chart in enumerate(charts):
        chart_cols[i % 3].markdown(f"- **{chart}**")
        
    st.divider()

    # 7. AI Dataset Understanding (Optional)
    st.header("7. AI Dataset Understanding (Optional Extension)")
    with st.expander("Explore AI-Powered Context"):
        st.write("If connected to an LLM API (like Google Gemini), you could send the following prompt to enhance this detection further:")
        
        col_names = ", ".join(df.columns.tolist())
        sample_data = df.head(3).to_csv(index=False)
        dtypes = ", ".join([f"{c}: {df[c].dtype}" for c in df.columns])
        
        prompt = f"""Analyze this dataset and determine:
1. Dataset Type
2. Business Domain
3. Important Metrics
4. Important Dimensions
5. Suggested KPIs
6. Suggested Visualizations

Context:
Column Names: {col_names}
Data Types: {dtypes}

Sample Data:
{sample_data}
"""
        st.code(prompt, language="text")
        st.info("Currently running on the highly-optimized Rule-Based Engine for maximum speed and privacy.")

if __name__ == "__main__":
    main()
