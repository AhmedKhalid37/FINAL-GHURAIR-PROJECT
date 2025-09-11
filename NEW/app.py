import streamlit as st
import requests
import json

# FastAPI backend URL - this will be the service name 'backend' in Docker Compose
API_URL = "http://backend:8000"

st.title("Helios Dynamics Agent-Driven ERP")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What can I help you with?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Send the prompt to the backend
                response = requests.post(f"{API_URL}/chat", json={"prompt": prompt})
                response.raise_for_status()
                assistant_response = response.json().get("response", "No response from agent.")

                st.markdown(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})

                # Handle visualizations if the response contains a chart spec
                if "chart_spec" in response.json():
                    chart_spec = response.json()["chart_spec"]
                    st.altair_chart(json.loads(chart_spec), use_container_width=True)

            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend server. Please ensure the backend is running.")
            except Exception as e:
                st.error(f"An error occurred: {e}")