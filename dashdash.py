import openai
import streamlit as st
import time

# Use the API key from st.secrets
openai.api_key = st.secrets["openai_api_key"]

assistant_id = "asst_rYaX0E7TOLCiR3Z3TXrCVC19"

client = openai

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

st.set_page_config(page_title="Numbers", page_icon=":speech_balloon:")

if st.sidebar.button("Start Chat"):
    st.session_state.start_chat = True
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

st.title("Numbers Assisstant")
st.write("Ask me anything about the numbers")

if st.button("Exit Chat"):
    st.session_state.messages = []  # Clear the chat history
    st.session_state.start_chat = False  # Reset the chat state
    st.session_state.thread_id = None

if st.session_state.start_chat:
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4-1106-preview"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me a question about the numbers!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=prompt
            )
        
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            instructions="As a data analyst assistant, your role involves managing and interpreting a dataset that contains information about client behavior and product usage. The dataset is structured as follows: Client List: The file includes a list of clients. Each client is associated with various products. Product Usage Columns: Each column in the dataset, apart from the 'week ending date' column, represents a different product. Examples of these columns include 'Adverse Letter 1', 'E-Verify', 'Clients With Orders', among others. These columns are crucial as they contain specific data points related to client interactions with the respective products. Week Ending Date Column: This particular column is labeled as 'week ending date'. It is important as it indicates the specific week when the product usage data was collected. This temporal marker is essential for understanding the time frame of the data. Understanding the Numbers: The numerical values in the product-related columns (like those mentioned above) are not arbitrary. They represent the number of transactions or instances of usage for each specific product. This is a key aspect as it reflects the frequency or intensity of product use by clients. Your Tasks: Your primary responsibilities include: Analyzing and interpreting this data. Answering questions related to the data, which could range from specific details about client-product interactions to broader trends observed in the dataset. Providing insights that could inform business practices, based on the patterns and trends you identify in the data. Your analysis and insights will be instrumental in understanding client behavior and improving business strategies related to product offerings and client engagement."
        )

        while run.status != 'completed':
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Process and display assistant messages
        assistant_messages_for_run = [
            message for message in messages 
            if message.run_id == run.id and message.role == "assistant"
        ]
        for message in assistant_messages_for_run:
            st.session_state.messages.append({"role": "assistant", "content": message.content[0].text.value})
            with st.chat_message("assistant"):
                st.markdown(message.content[0].text.value)

else:
    st.write("Click 'Start Chat' to begin.")
