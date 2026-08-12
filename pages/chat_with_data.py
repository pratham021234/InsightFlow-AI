import streamlit as st
import pandas as pd
from services.chat_engine import (
    detect_intent,
    extract_entities,
    handle_metadata_questions,
    execute_query,
    generate_ai_explanation
)

st.set_page_config(page_title="Chat With Data", page_icon="💬", layout="wide")

def get_suggested_questions(dataset_type):
    if dataset_type == "Sales":
        return [
            "Which product generates highest revenue?", 
            "Which region performs best?", 
            "Show revenue trend.", 
            "Top 10 customers by revenue."
        ]
    elif dataset_type == "HR":
        return [
            "Average salary by department.", 
            "Which department has highest attrition?", 
            "Top paying departments.", 
            "How many rows exist?"
        ]
    elif dataset_type == "Finance":
        return [
            "Which category generates the most expense?", 
            "Show profit trends.", 
            "Compare income across divisions.", 
            "What are the biggest risks?"
        ]
    else:
        return [
            "Which category has the highest value?", 
            "Show distribution of the main metric.", 
            "How many rows exist?", 
            "What columns are available?"
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
    st.markdown("### Natural Language Analytics Engine")
    st.divider()

    df = st.session_state.get("cleaned_df", st.session_state.get("original_df"))
    if df is None:
        st.warning("No dataset found. Please upload a dataset first.")
        return

    dataset_type = st.session_state.get("dataset_type", "General Dataset")
    
    # Init Chat State
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
        append_message("assistant", f"Hello! I am your AI Data Analyst. Your '{dataset_type}' dataset is loaded and ready. What would you like to know?")

    # Suggested Questions Layout
    st.write("**Suggested Questions:**")
    suggestions = get_suggested_questions(dataset_type)
    cols = st.columns(4)
    quick_query = None
    for i, sq in enumerate(suggestions):
        if cols[i].button(sq, use_container_width=True):
            quick_query = sq

    st.divider()
    
    # Render Chat History
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("fig") is not None:
                st.plotly_chart(msg["fig"], use_container_width=True, config={'displaylogo': False})
            if msg.get("data") is not None:
                with st.expander("View Raw Data"):
                    st.dataframe(msg["data"], use_container_width=True)

    # Handle Input
    user_input = st.chat_input("Ask a question about your data...")
    query = quick_query if quick_query else user_input

    if query:
        # Display user message
        with st.chat_message("user"):
            st.markdown(query)
        append_message("user", query)
        
        # Process response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing data..."):
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
                    if not measure or not dimension:
                        err = f"I couldn't identify the specific columns needed for this query. I inferred Measure: '{measure}', Dimension: '{dimension}'. Please be more specific with column names."
                        st.markdown(err)
                        append_message("assistant", err)
                    else:
                        result = execute_query(df, intent, measure, dimension)
                        
                        if "error occurred" in result["text"]:
                            st.error(result["text"])
                            append_message("assistant", result["text"])
                        else:
                            ai_exp = generate_ai_explanation(result["text"], query)
                            final_text = f"{result['text']}\n\n{ai_exp}"
                            
                            st.markdown(final_text)
                            if result["fig"] is not None:
                                st.plotly_chart(result["fig"], use_container_width=True, config={'displaylogo': False})
                            if result["data"] is not None:
                                with st.expander("View Raw Data"):
                                    st.dataframe(result["data"], use_container_width=True)
                                    
                            append_message("assistant", final_text, result["data"], result["fig"])
                        
    # Export Chat Tools
    with st.sidebar:
        st.header("Chat Tools")
        if st.button("Clear Chat History"):
            st.session_state["chat_history"] = []
            st.rerun()
            
        st.divider()
        st.write("Export Conversation")
        if len(st.session_state["chat_history"]) > 1:
            chat_txt = "\n\n".join([f"{m['role'].upper()}:\n{m['content']}" for m in st.session_state["chat_history"]])
            st.download_button(
                label="Download Chat Log (TXT)", 
                data=chat_txt, 
                file_name="InsightFlow_Chat_Export.txt", 
                mime="text/plain", 
                use_container_width=True
            )

if __name__ == "__main__":
    main()
