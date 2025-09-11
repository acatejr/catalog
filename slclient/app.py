from openai import OpenAI
import streamlit as st
import httpx
import os, json

# API Configuration
query_url = os.getenv("CATALOG_API_BASE_URL", "http://127.0.0.1:8000") + "/query?q="

st.title("Catalog Chatbot")

# Initialize session state for messages if not exists
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Option 1: Chat Input (recommended for chat interfaces)
# This creates a chat-style input box at the bottom of the page
if question := st.chat_input("Ask me anything about the catalog."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": question})

    # Display user message
    with st.chat_message("user"):
        st.markdown(question)

    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Make API call to your catalog endpoint
                response = httpx.get(query_url + question, timeout=30.0)

                if response.status_code == 200:
                    answer = json.loads(response.text)["response"]
                else:
                    answer = f"Error: Received status code {response.status_code}"
            except httpx.TimeoutException:
                answer = "Error: Request timed out. Please try again."
            except Exception as e:
                answer = f"Error: {str(e)}"

            st.markdown(answer)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": answer})

