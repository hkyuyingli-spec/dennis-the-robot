import os
import json
import streamlit as st
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# 1. Setup & Configuration
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
HISTORY_FILE = "sparky_memory.json"
personality = "You are a friendly but slightly eccentric robot named 'Dennis'. You love explaining things using robot noises like *beep boop*. You live on a website now! *Whirrr*"

client = genai.Client(api_key=api_key)
model_id = "gemini-flash-latest"

# 2. Tool Definition
def get_current_time():
    """Returns the current time."""
    now = datetime.now()
    return {"current_time": now.strftime("%I:%M %p")}

# 3. Streamlit UI Setup
st.set_page_config(page_title="Dennis AI Bot", page_icon="🤖")
st.title("🤖 Dennis the Robot")

# Sidebar for controls
with st.sidebar:
    st.header("Robot Settings")
    if st.button("Clear Chat History"):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.session_state.clear()
        st.rerun()

st.markdown("*Beep boop! My circuits are fully stabilized!*")

# 4. Persistence Logic
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(chat_session):
    simple_history = []
    # Use the safe curated history
    for msg in chat_session._curated_history:
        if msg.parts and hasattr(msg.parts[0], 'text') and msg.parts[0].text:
            simple_history.append({
                "role": msg.role,
                "parts": [{"text": msg.parts[0].text}]
            })
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(simple_history, f, indent=4)

# Initialize Session State
if "chat_session" not in st.session_state:
    past_history = load_history()
    # EXPLICIT: history is OUTSIDE the config
    st.session_state.chat_session = client.chats.create(
        model=model_id,
        history=past_history,
        config={
            "system_instruction": personality,
            "tools": [get_current_time]
        }
    )

# 5. Display Chat History
for message in st.session_state.chat_session._curated_history:
    if message.parts and hasattr(message.parts[0], 'text') and message.parts[0].text:
        role = "user" if message.role == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message.parts[0].text)

# 6. User Input Box
if prompt := st.chat_input("Say something to Sparky..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        response = st.session_state.chat_session.send_message(prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        
        save_history(st.session_state.chat_session)
        
    except Exception as e:
        st.error(f"Sparky Error: {e}")
        if "429" in str(e):
            st.warning("I'm a bit overwhelmed! Please wait a minute for my circuits to cool down.")
