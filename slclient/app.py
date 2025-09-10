import streamlit as st

# st.title("🎈 My new app")
# st.write(
#     "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
# )

st.title("Data Catalog")
# st.write("Welcome to the Data Catalog app!")

prompt = st.chat_input("Ask me anything about the data catalog.")
if prompt:
    st.write(f"User has sent the following prompt: {prompt}")
