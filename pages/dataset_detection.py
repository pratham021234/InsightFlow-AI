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
from utils.session_manager import get_active_df

st.set_page_config(page_title="Dataset Intelligence", page_icon="🧠", layout="wide")

def main():
    st.title("Dataset Intelligence")
    st.markdown("### Heuristic Domain Classification & Contextual Entity Recognition")
    st.divider()

    df = get_active_df()
    if df is None:
        st.warning("No dataset found. Please upload or load a sample dataset on the **Upload** page first.")
        st.info("Navigate to the main page from the left sidebar to ingest a dataset.")
        return

    with st.spinner("Evaluating column ontology and semantic domain signatures..."):
        dataset_type, confidence, all_scores = detect_dataset_type(df)
        domain_name = dataset_type if dataset_type == "General Dataset" else f"{dataset_type} Dataset"
        description = generate_dataset_description(dataset_type)
        entities = extract_business_entities(df, dataset_type)
        kpis = generate_kpi_suggestions(dataset_type)
        charts = generate_chart_suggestions(dataset_type)
        
        save_detection_results(dataset_type, confidence, entities, description, kpis, charts)

    # 1. Detection Summary
    st.header("1. Domain Classification Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Identified Domain Signature:**\n\n### {domain_name}")
    with col2:
        st.success(f"**Classification Confidence:**\n\n### {confidence:.1f}%")
        
    st.divider()

    # 2. Confidence Scores
    st.header("2. Domain Confidence Distribution")
    if all_scores:
        score_df = pd.DataFrame(list(all_scores.items()), columns=["Business Domain", "Match Confidence (%)"])
        score_df = score_df.sort_values(by="Match Confidence (%)", ascending=False).head(5)
        st.dataframe(score_df, use_container_width=True)
    else:
        st.write("No distinct domain signatures found.")
        
    st.divider()

    # 3. Business Description
    st.header("3. Contextual Domain Scope")
    st.markdown(f"> {description}")
    
    st.divider()

    # 4. Business Entities
    st.header("4. Key Extracted Entities & Attributes")
    if entities:
        cols = st.columns(min(len(entities), 6))
        for i, entity in enumerate(entities[:6]):
            cols[i].button(f"📌 {entity}", disabled=True, key=f"entity_{i}", use_container_width=True)
    else:
        st.write("No specific business entities isolated.")

    st.divider()

    # 5. KPI Recommendations
    st.header("5. Domain-Tailored KPI Recommendations")
    st.caption("These metrics are automatically synthesized and tracked in the KPI Dashboard:")
    kpi_cols = st.columns(3)
    for i, kpi in enumerate(kpis):
        kpi_cols[i % 3].markdown(f"• **{kpi}**")

    st.divider()

    # 6. Visualization Recommendations
    st.header("6. Recommended Analytical Visualizations")
    st.caption("Visual patterns prioritized for this domain:")
    chart_cols = st.columns(3)
    for i, chart in enumerate(charts):
        chart_cols[i % 3].markdown(f"• **{chart}**")
        
    st.divider()

    # 7. AI Dataset Understanding Prompt Template
    st.header("7. AI Semantic Prompt Context")
    with st.expander("Inspect Prepared Analytical Prompt"):
        st.write("Structured context prepared for Google Gemini semantic analysis:")
        col_names = ", ".join(df.columns.tolist())
        sample_data = df.head(3).to_csv(index=False)
        dtypes = ", ".join([f"{c}: {df[c].dtype}" for c in df.columns])
        
        prompt = f"""Analyze this dataset and determine:
1. Dataset Type & Specific Sub-domain
2. Primary Measures & Dimensions
3. High-Priority KPIs
4. Recommended Diagnostic Visualizations

Context:
Columns: {col_names}
Data Types: {dtypes}
Sample Data:
{sample_data}"""
        st.code(prompt, language="text")

if __name__ == "__main__":
    main()
