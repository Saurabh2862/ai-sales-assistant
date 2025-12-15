import streamlit as st
import requests
import os
import pandas as pd

# ================= CONFIG =================
API_URL = os.getenv("API_URL", "http://localhost:8000/chat")

st.set_page_config(
    page_title="AI Sales Assistant",
    page_icon="🤖",
    layout="wide"
)

# ================= THEME =================
st.markdown("""
<style>
body { background-color: #0e1117; }
.stChatMessage { border-radius: 10px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# ================= STATE =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ================= SIDEBAR =================
with st.sidebar:
    st.title("📊 AI Sales Assistant")

    st.markdown("### Suggested questions")
    suggestions = [
        "Total sales in Jan 2024",
        "Top 5 brands by sales in 2024",
        "Sales by salesman in Jan 2024",
        "Active stores in Feb 2024",
        "Sales of Delphy Cheese in Jan 2024"
    ]

    for q in suggestions:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

    st.divider()

    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.session_state.pending_question = None
        st.experimental_rerun()

    st.caption("✔ Deterministic backend • No hallucinations")

# ================= HEADER =================
st.title("🤖 Sales & Document Chatbot")
st.caption("Ask questions about sales, stores, brands, and performance")

# ================= CHAT HISTORY =================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ================= INPUT =================
user_input = st.chat_input("Ask a question (e.g. Total sales in Jan 2024)")

# unify sidebar + chat input
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None

# ================= PROCESS =================
if user_input:
    # ---- USER MESSAGE ----
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # ---- ASSISTANT ----
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

            except Exception as e:
                st.error("❌ Backend error. Please try again.")

    # ---- SAVE ASSISTANT MESSAGE ----
    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

# ================= DOWNLOAD =================
if st.session_state.last_result is not None:
    st.divider()
    st.markdown("### 📥 Download Result")

    csv = st.session_state.last_result.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="sales_result.csv",
        mime="text/csv"
    )
