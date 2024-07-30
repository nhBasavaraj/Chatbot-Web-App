import os
import streamlit as st
import json
import google.generativeai as genai
from openai import OpenAI
from datetime import datetime

# Directory to save conversations
CONVERSATION_DIR = "conversations"
if not os.path.exists(CONVERSATION_DIR):
    os.makedirs(CONVERSATION_DIR)

# Function to save conversation to a file
def save_conversation(conversation, filename):
    with open(os.path.join(CONVERSATION_DIR, filename), 'w') as f:
        json.dump(conversation, f)

# Function to load conversation from a file
def load_conversation(filename):
    with open(os.path.join(CONVERSATION_DIR, filename), 'r') as f:
        return json.load(f)

# Function to list all saved conversations
def list_conversations():
    return os.listdir(CONVERSATION_DIR)

# Function to delete a conversation file
def delete_conversation(filename):
    os.remove(os.path.join(CONVERSATION_DIR, filename))

# Sidebar for LLM selection, API keys, and conversation history
with st.sidebar:
    llm_model = st.selectbox("Select LLM Model", ["Gemini-pro", "OpenAI GPT-3.5"])

    if llm_model == "Gemini-pro":
        gemini_api_key = st.text_input("Gemini API Key", key="chatbot_api_key", type="password")
        # "[Get a Gemini API key](https://aistudio.google.com/app/apikey)"
    elif llm_model == "OpenAI GPT-3.5":
        openai_api_key = st.text_input("OpenAI API Key", key="openai_api_key", type="password")
        # "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"

    if st.button("New Chat"):
        # Save the current conversation
        if st.session_state["messages"]:
            save_conversation(st.session_state["messages"], st.session_state["current_conversation_file"])
        # Start a new chat
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]
        # Update the conversation file tracking
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        st.session_state["current_conversation_file"] = f"{timestamp}"

    # List all saved conversations
    st.write("Conversation History")
    conversation_files = list_conversations()
    conversation_files.reverse()
    for filename in conversation_files:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"{filename}"):
                st.session_state.messages = load_conversation(filename)
                st.session_state["current_conversation_file"] = filename 
        with col2:
            if st.button(f"🗑", key=f"delete_{filename}"):
                delete_conversation(filename)
                st.rerun()

# Save conversation automatically whenever a new message is added
def auto_save_conversation():
    save_conversation(st.session_state.messages, st.session_state["current_conversation_file"])


# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
if "current_conversation_file" not in st.session_state:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    st.session_state["current_conversation_file"] = f"{timestamp}"


st.title("Chatbot")

# Display chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Configure LLM based on selection
if llm_model == "Gemini-pro":
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(model_name="gemini-pro")
    else:
        st.info("Please add your Gemini API key to continue.")
        st.stop()

elif llm_model == "OpenAI GPT-3.5":
    if openai_api_key:
        client = OpenAI(api_key=openai_api_key)
    else:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

# Chat input and response
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if llm_model == "Gemini-pro":
        chat_session = model.start_chat()
        conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
        prompt_with_history = f"{conversation_history}\nuser: {prompt}"
        response = chat_session.send_message(content=prompt_with_history)
        msg = response.text

    elif llm_model == "OpenAI GPT-3.5":
        conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
        prompt_with_history = f"{conversation_history}\nuser: {prompt}"

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_with_history},
            ],
            model="gpt-3.5-turbo",
        )
        msg = chat_completion.choices[0].message.content.strip()

    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

    # Automatically save the conversation after each user message
    save_conversation(st.session_state.messages, st.session_state["current_conversation_file"])
