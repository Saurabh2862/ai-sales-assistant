import streamlit as st
import requests
import os
import pandas as pd


API_URL = os.getenv(
    "API_URL",
    "http://localhost:8000/chat"
)

PDF_COMPARE_URL = os.getenv(
    "PDF_COMPARE_URL",
    "http://localhost:8000/pdf/compare"
)


st.set_page_config(
    page_title="AI Sales Assistant",
    page_icon="🤖",
    layout="wide"
)


st.markdown("""
<style>
body { background-color: #0e1117; }
.stChatMessage { border-radius: 10px; padding: 10px; }
</style>
""", unsafe_allow_html=True)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


with st.sidebar:
    st.title("📊 AI Sales Assistant")

    mode = st.radio(
        "Choose Mode",
        ["📊 Sales Analytics", "📄 Document Comparison"]
    )

    st.divider()

    
    if mode == "📊 Sales Analytics":
        st.markdown("### 💡 Suggested questions")
        suggestions = [
            "Total sales in Jan 2024",
            "Top 5 brands by sales in 2024",
            "Sales by salesman in Jan 2024",
            "Sales of Delphy Cheese in Jan 2024",
            "Promo vs non-promo sales in 2024"
        ]

        for q in suggestions:
            if st.button(q, use_container_width=True):
                st.session_state.pending_question = q

    if mode == "📄 Document Comparison":
        st.markdown("### 📄 Upload Documents")

        po_file = st.file_uploader(
            "Purchase Order (PDF)",
            type=["pdf"]
        )

        pi_file = st.file_uploader(
            "Proforma Invoice (PDF)",
            type=["pdf"]
        )

        run_compare = st.button(
            "🔍 Compare PO vs PI",
            use_container_width=True
        )

    st.divider()

    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.session_state.pending_question = None
        st.experimental_rerun()

    st.caption("✔ Deterministic backend • No hallucinations")


st.title("🤖 Sales & Document Chatbot")
st.caption("Deterministic AI for Sales Analytics and Document RAG")


if mode == "📊 Sales Analytics":

    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    
    user_input = st.chat_input(
        "Ask a question (e.g. Total sales in Jan 2024)"
    )

    if st.session_state.pending_question:
        user_input = st.session_state.pending_question
        st.session_state.pending_question = None

    if user_input:
        
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("user"):
            st.markdown(user_input)

        answer = "❌ Could not process the request."

       
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        API_URL,
                        json={"question": user_input},
                        timeout=60
                    )

                    if response.status_code != 200:
                        raise Exception(response.text)

                    data = response.json()

                    answer = data.get("answer", "No answer returned.")
                    table = data.get("table")

                    st.markdown(answer)

                    if table:
                        df = pd.DataFrame(table)
                        st.session_state.last_result = df
                        st.dataframe(df, use_container_width=True)

                except Exception:
                    st.error(
                        "Backend is waking up or unavailable. "
                        "Please retry in 20–30 seconds."
                    )

        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )


if (
    mode == "📊 Sales Analytics"
    and st.session_state.last_result is not None
):
    st.divider()
    st.markdown("### 📥 Download Result")

    csv = (
        st.session_state.last_result
        .to_csv(index=False)
        .encode("utf-8")
    )

    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="sales_result.csv",
        mime="text/csv"
    )


if mode == "📄 Document Comparison":

    if 'run_compare' in locals() and run_compare:
        if not po_file or not pi_file:
            st.error("Please upload both PO and PI PDFs.")
        else:
            with st.spinner("Comparing documents..."):
                try:
                    files = {
                        "po": ("po.pdf", po_file.getvalue(), "application/pdf"),
                        "pi": ("pi.pdf", pi_file.getvalue(), "application/pdf"),
                    }

                    response = requests.post(
                        PDF_COMPARE_URL,
                        files=files,
                        timeout=120
                    )

                    if response.status_code != 200:
                        raise Exception(response.text)

                    data = response.json()

                    st.success("Comparison completed successfully")

                    st.markdown("### 📊 Summary")
                    st.json(data.get("summary", {}))

                    st.markdown("### ❗ Discrepancies")
                    discrepancies = data.get("discrepancies", [])

                    if discrepancies:
                        st.dataframe(
                            pd.DataFrame(discrepancies),
                            use_container_width=True
                        )
                    else:
                        st.info("No discrepancies found.")

                except Exception:
                    st.error(
                        "Document comparison failed. "
                        "Please try again."
                    )
