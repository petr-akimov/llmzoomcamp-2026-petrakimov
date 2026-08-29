import os
import requests
import streamlit as st

# Read backend URL from environment variable (default for local debugging)
RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RAG Assistant UI",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 RAG Knowledge Assistant")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for controls and configuration
with st.sidebar:
    st.header("⚙️ Settings")
    k_val = st.slider("Context Chunks (k)", min_value=1, max_value=10, value=3)
    
    st.divider()
    st.subheader("System Status")
    try:
        res = requests.get(f"{RAG_API_URL}/healthz", timeout=3)
        if res.status_code == 200:
            st.success("RAG Backend: Connected")
        else:
            st.error(f"RAG Backend Error: HTTP {res.status_code}")
    except Exception as e:
        st.error(f"RAG Backend: Disconnected ({str(e)})")

# Render previous messages from session history
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Render source metadata if present
        if msg.get("sources"):
            with st.expander("📚 Sources"):
                for src in msg["sources"]:
                    st.write(f"- `{src}`")
        
        # User feedback UI for assistant responses
        if msg["role"] == "assistant" and i == len(st.session_state.messages) - 1:
            col1, col2, col3 = st.columns([1, 1, 8])
            with col1:
                if st.button("👍", key=f"like_{i}"):
                    try:
                        requests.post(
                            f"{RAG_API_URL}/api/v1/feedback",
                            json={"sentiment": "positive"},
                            timeout=5,
                        )
                        st.toast("Feedback recorded: Positive!", icon="✅")
                    except Exception as e:
                        st.error(f"Failed to send feedback: {e}")
            with col2:
                if st.button("👎", key=f"dislike_{i}"):
                    try:
                        requests.post(
                            f"{RAG_API_URL}/api/v1/feedback",
                            json={"sentiment": "negative"},
                            timeout=5,
                        )
                        st.toast("Feedback recorded: Negative!", icon="⚠️")
                    except Exception as e:
                        st.error(f"Failed to send feedback: {e}")

# Process user prompt input
if prompt := st.chat_input("Ask a question based on knowledge base..."):
    # Append user question to session state and render
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Fetch metadata and document sources first
        sources = []
        try:
            meta_res = requests.post(
                f"{RAG_API_URL}/api/v1/query",
                json={"question": prompt, "k": k_val},
                timeout=10,
            )
            if meta_res.status_code == 200:
                sources = meta_res.json().get("sources", [])
        except Exception:
            pass  # Proceed to streaming answer even if source metadata request fails

        # Stream response chunks in real time
        try:
            with requests.post(
                f"{RAG_API_URL}/api/v1/query/stream",
                json={"question": prompt, "k": k_val},
                stream=True,
                timeout=60,
            ) as response:
                if response.status_code == 200:
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                else:
                    full_response = f"Error: Received status code {response.status_code}"
                    message_placeholder.error(full_response)
        except Exception as e:
            full_response = f"Connection error: {str(e)}"
            message_placeholder.error(full_response)

        # Render retrieved sources below the generated text
        if sources:
            with st.expander("📚 Sources"):
                for src in sources:
                    st.write(f"- `{src}`")

        # Persist complete assistant answer into history
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": full_response,
                "sources": sources,
            }
        )
        st.rerun()