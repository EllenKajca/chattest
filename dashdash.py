import streamlit as st
from openai import OpenAI, OpenAIError
import time

# Define the function to fetch the latest run response
def get_latest_run_response(thread_id):
    try:
        runs_response = client.beta.threads.runs.list(thread_id=thread_id)
        if runs_response.data:
            # Assume the latest run is the last in the list
            return runs_response.data[-1]
    except OpenAIError as e:
        st.error(f"Error fetching run response: {e}")
        return None


# Function to check the status of the last run and wait until it is complete
def wait_for_run_completion(thread_id):
    run_completed = False
    while not run_completed:
        try:
            runs_response = client.beta.threads.runs.list(thread_id=thread_id)
            if runs_response.data:
                latest_run = runs_response.data[-1]
                if latest_run.status in ['completed', 'failed']:
                    run_completed = True
                else:
                    # Wait for a bit before checking again
                    time.sleep(1)
        except OpenAIError as e:
            st.error(f"Error fetching run status: {e}")
            break
    

def display_messages(messages):
    for msg in messages:
        st.write(f"{msg['role'].title()}: {msg['content']}")

client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("💬 Chatbot")

assistant_id = "asst_rYaX0E7TOLCiR3Z3TXrCVC19"

if 'thread_id' not in st.session_state:
    try:
        thread = client.beta.threads.create()
        st.session_state['thread_id'] = thread.id
    except OpenAIError as e:
        st.error(f"Error creating thread: {e}")
    st.session_state['messages'] = []

display_messages(st.session_state.get('messages', []))

with st.form(key='user_input_form'):
    user_input = st.text_input('Type your message here:')
    submit_button = st.form_submit_button('Send')

if submit_button and user_input:
    # Wait for any active runs to complete before sending a new message
    if 'run_active' in st.session_state and st.session_state['run_active']:
        with st.spinner('Waiting for the assistant to respond...'):
            wait_for_run_completion(st.session_state['thread_id'])

    st.session_state.messages.append({"role": "user", "content": user_input})
    try:
        client.beta.threads.messages.create(
            thread_id=st.session_state['thread_id'],
            role="user",
            content=user_input
        )
        run_response = client.beta.threads.runs.create(
            thread_id=st.session_state['thread_id'],
            assistant_id=assistant_id
        )
        if run_response.status == 'in_progress':
            st.session_state['run_active'] = True
    except OpenAIError as e:
        st.error(f"Error sending message or creating run: {e}")

# Check the status of the latest run outside the condition to avoid blocking user input
latest_run = get_latest_run_response(st.session_state['thread_id'])
if latest_run and latest_run.status in ['completed', 'failed']:
    st.session_state['run_active'] = False
    if latest_run.status == 'completed':
        for msg in latest_run.messages:
            if msg.role == 'assistant':
                st.session_state.messages.append({"role": "assistant", "content": msg.content})
                display_messages([{"role": "assistant", "content": msg.content}])
