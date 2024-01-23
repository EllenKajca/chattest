

import streamlit as st
from openai import OpenAI, OpenAIError
import time

# Function to fetch the latest run response
def get_latest_run_response(thread_id):
    while True:
        try:
            runs_response = client.beta.threads.runs.list(thread_id=thread_id)
            if runs_response.data:
                latest_run = runs_response.data[-1]
                if latest_run.status == 'queued':
                    # Update the user on the status
                    st.warning('The system is busy, your request is queued. Waiting for the assistant to respond...')
                    time.sleep(5)  # Wait for 5 seconds before checking the status again
                elif latest_run.status in ['completed', 'failed']:
                    return latest_run
        except OpenAIError as e:
            st.error(f"Error fetching run response: {e}")
            return None

# Function to retrieve the latest messages from a thread
def get_assistant_messages(thread_id):
    try:
        messages_response = client.beta.threads.messages.list(thread_id=thread_id)
        assistant_messages = [msg for msg in messages_response.data if msg['role'] == 'assistant']
        return assistant_messages
    except OpenAIError as e:
        st.error(f"Error fetching messages: {e}")
        return []

# Function to display messages
def display_messages(messages):
    for msg in messages:
        st.write(f"{msg['role'].title()}: {msg['content']}")

# Initialize the OpenAI client
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("💬 Chatbot")

# Replace with your assistant's ID
assistant_id = "asst_rYaX0E7TOLCiR3Z3TXrCVC19"

# Initialize session state for thread if it doesn't exist
if 'thread_id' not in st.session_state:
    try:
        thread = client.beta.threads.create()
        st.session_state['thread_id'] = thread.id
        st.session_state['messages'] = []
    except OpenAIError as e:
        st.error(f"Error creating thread: {e}")

# Display previous messages
display_messages(st.session_state.get('messages', []))

# Create a form for user input
with st.form(key='user_input_form'):
    user_input = st.text_input('Type your message here:')
    submit_button = st.form_submit_button('Send')

# Process user input
if submit_button and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    try:
        # Send the user message to the assistant
        client.beta.threads.messages.create(
            thread_id=st.session_state['thread_id'],
            role="user",
            content=user_input
        )
        st.info("User message sent, awaiting run to initiate...")
        # Create a run
        run_response = client.beta.threads.runs.create(
            thread_id=st.session_state['thread_id'],
            assistant_id=assistant_id
        )
        # Poll for run status if queued or in progress
        if run_response.status in ['in_progress', 'queued']:
            st.session_state['run_active'] = True
            with st.spinner("The system is currently busy, your request is being processed. Please wait..."):
                latest_run = get_latest_run_response(st.session_state['thread_id'])
                if latest_run and latest_run.status == 'completed':
                    st.success("The assistant has responded.")
                    # Fetch and display messages
                    assistant_messages = get_assistant_messages(st.session_state['thread_id'])
                    for msg in assistant_messages:
                        st.session_state.messages.append({"role": "assistant", "content": msg['content']})
                    display_messages(assistant_messages)
                elif latest_run and latest_run.status == 'failed':
                    st.error("The assistant failed to process the request.")
        else:
            st.error(f"Run could not be initiated, status: {run_response.status}")
    except OpenAIError as e:
        st.error(f"Error sending message or creating run: {e}")

