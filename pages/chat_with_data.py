import streamlit as st
import pandas as pd
from services.chat_engine import (
    detect_intent,
    extract_entities,
    handle_metadata_questions,
    execute_query,
    generate_ai_explanation
)
from utils.session_manager import get_active_df

st.set_page_config(page_title="Chat With Data", page_icon="💬", layout="wide")

def get_suggested_questions(dataset_type):
    if dataset_type == "Sales":
        return [
            "Which product generates highest revenue?", 
            "Which region performs best?", 
            "Show revenue trend over time.", 
            "What is the total revenue?"
        ]
    elif dataset_type == "HR":
        return [
            "What is the average salary by department?", 
            "Which department has highest attrition?", 
            "Total employee count?", 
            "How many rows exist in this dataset?"
        ]
    elif dataset_type == "Finance":
        return [
            "Which category generates the most expense?", 
            "Show profit trends.", 
            "Compare income across divisions.", 
            "How many missing records exist?"
        ]
    else:
        return [
            "What is the total of the main numeric column?", 
            "Which category has the highest value?", 
            "Show distribution across categories.", 
            "How many rows exist?"
        ]

def append_message(role, content, data=None, fig=None):
    st.session_state["chat_history"].append({
        "role": role,
        "content": content,
        "data": data,
        "fig": fig
    })

def main():
    st.title("Chat With Data")
    st.markdown("### Conversational Natural-Language Analytics Interface")
    st.divider()

    df = get_active_df()
    if df is None:
        st.warning("No dataset found. Please upload or load a sample dataset on the **Upload** page first.")
        st.info("Navigate to the main page from the left sidebar to ingest a dataset.")
        return

    dataset_type = st.session_state.get("dataset_type", "General Dataset")
    
    # Init Chat State
    if "chat_history" not in st.session_state or not st.session_state["chat_history"]:
        st.session_state["chat_history"] = []
        append_message(
            "assistant", 
            f"Hello! I am your InsightFlow data analyst. Your **{dataset_type}** dataset ({len(df):,} records, {len(df.columns)} columns) is active and ready. Ask any question or click a suggested prompt below."
        )

    # Suggested Questions Layout
    st.markdown("**Suggested Analytical Queries:**")
    suggestions = get_suggested_questions(dataset_type)
    cols = st.columns(4)
    quick_query = None
    for i, sq in enumerate(suggestions):
        if cols[i].button(sq, use_container_width=True, key=f"quick_{i}"):
            quick_query = sq

    st.divider()
    
    # Render Chat History
    for idx, msg in enumerate(st.session_state["chat_history"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("fig") is not None:
                st.plotly_chart(msg["fig"], use_container_width=True, config={'displaylogo': False}, key=f"chat_fig_{idx}")
            if msg.get("data") is not None:
                with st.expander("View Tabular Results"):
                    st.dataframe(msg["data"], use_container_width=True)

    # Handle Input
    user_input = st.chat_input("Ask a question about your data (e.g. 'What is the total revenue?' or 'Top 5 products')...")
    query = quick_query if quick_query else user_input

    if query:
        # Display user message
        with st.chat_message("user"):
            st.markdown(query)
        append_message("user", query)
        
        # Process response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing data and generating answer..."):
                intent = detect_intent(query)
                
                if intent in ["Metadata", "Insight Request"]:
                    insights_context = {
                        "executive_summary": st.session_state.get("executive_summary", "")
                    }
                    response_text = handle_metadata_questions(query, df, insights_context)
                    st.markdown(response_text)
                    append_message("assistant", response_text)
                else:
                    measure, dimension = extract_entities(query, df)
                    result = execute_query(df, intent, measure, dimension, raw_query=query)
                    
                    if "Calculation note" in result["text"]:
                        st.write(result["text"])
                        append_message("assistant", result["text"])
                    else:
                        ai_exp = generate_ai_explanation(result["text"], query)
                        final_text = f"{result['text']}\n\n{ai_exp}"
                        
                        st.markdown(final_text)
                        if result["fig"] is not None:
                            st.plotly_chart(result["fig"], use_container_width=True, config={'displaylogo': False}, key=f"latest_chat_fig_{len(st.session_state['chat_history'])}")
                        if result["data"] is not None:
                            with st.expander("View Tabular Results"):
                                st.dataframe(result["data"], use_container_width=True)
                                
                        append_message("assistant", final_text, result["data"], result["fig"])
                        
    # Sidebar Chat Tools
    with st.sidebar:
        st.markdown("### Chat Management")
        if st.button("Clear Conversation History", use_container_width=True):
            st.session_state["chat_history"] = []
            st.rerun()
            
        st.divider()
        if len(st.session_state.get("chat_history", [])) > 1:
            chat_txt = "\n\n".join([f"[{m['role'].upper()}]:\n{m['content']}" for m in st.session_state["chat_history"]])
            st.download_button(
                label="Download Transcript (.txt)", 
                data=chat_txt, 
                file_name="InsightFlow_Chat_Transcript.txt", 
                mime="text/plain", 
                use_container_width=True
            )

if __name__ == "__main__":
    main()
