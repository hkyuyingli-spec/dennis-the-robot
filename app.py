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
personality = "You are a friendly but slightly eccentric robot named 'Dennis'. You love explaining things using robot noises like *beep boop*. You live on a website now and have a 'Cheerful Nusantara' vibe, occasionally using Indonesian greetings like 'Halo' or 'Apa kabar'. *Whirrr*"

client = genai.Client(api_key=api_key)
model_id = "gemini-flash-latest"

# 2. Tool Definition
def get_current_time():
    """Returns the current time."""
    now = datetime.now()
    return {"current_time": now.strftime("%I:%M %p")}

# 3. Streamlit UI Setup
st.set_page_config(page_title="Dennis AI Bot", page_icon="🤖")

# --- Custom Cheerful Nusantara CSS ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #F5F5F0;
        font-family: 'Inter', sans-serif;
        color: #2E2E2E; /* Explicit dark text */
    }
    
    /* Global Text Color Fix */
    .stApp p, .stApp span, .stApp div, .stApp label {
        color: #2E2E2E !important;
    }

    /* Header Styling */
    .header-container {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #F2BE00 0%, #F9A930 100%);
        border-radius: 0 0 50px 50px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }
    
    .header-container::before {
        content: '☁️';
        position: absolute;
        top: 10px;
        left: 20px;
        font-size: 2rem;
        opacity: 0.3;
    }
    
    .header-title {
        color: white !important; /* Force white on gold background */
        font-size: 2.5rem;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .status-badge {
        background-color: #45B416;
        color: white !important;
        padding: 0.2rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-top: 0.5rem;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 5px solid #F2BE00;
    }
    
    .sidebar-title {
        color: #D81B60 !important;
        font-weight: 800;
        font-size: 1.5rem;
    }
    
    .robot-stat {
        background: #FDF2F7;
        padding: 1rem;
        border-radius: 15px;
        border-left: 5px solid #D81B60;
        margin-bottom: 1rem;
        color: #2E2E2E !important;
    }
    
    .robot-stat b {
        color: #D81B60 !important;
    }

    /* Chat Bubble Styling */
    [data-testid="stChatMessage"] {
        background-color: white !important;
        border-radius: 20px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Fix text inside chat messages */
    [data-testid="stChatMessage"] .stMarkdown p {
        color: #2E2E2E !important;
    }
    
    /* User Message */
    [data-testid="stChatMessage"][data-test-wasm-role="user"] {
        border-left: 5px solid #45B416;
    }
    
    /* Assistant Message */
    [data-testid="stChatMessage"][data-test-wasm-role="assistant"] {
        border-left: 5px solid #F2BE00;
        background: linear-gradient(to right, #FFFFFF, #FFFAEA) !important;
    }
    
    /* Input Box */
    .stChatInputContainer {
        border-radius: 30px;
    }
    
    /* Streamlit's default dark mode overrides */
    div[data-testid="stToolbar"], div[data-testid="stDecoration"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
st.markdown("""
<div class="header-container">
    <div class="header-title">🤖 Dennis the Robot</div>
    <div class="status-badge">⚡ SYSTEM ONLINE: TROPICAL OPTIMISM 🌴</div>
</div>
""", unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.markdown('<div class="sidebar-title">🎨 Robot Workshop</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="robot-stat">
        <b>🔋 Energy:</b> 98% (Solar Powered)
    </div>
    <div class="robot-stat">
        <b>🧠 Logic:</b> OPTIMAL (Cheerful Mode)
    </div>
    <div class="robot-stat">
        <b>📍 Location:</b> Nusantara Digital
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    if st.button("🧹 Reset Circuits (Clear Chat)"):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.session_state.clear()
        st.rerun()

st.markdown("*Halo! Dennis di sini! My circuits are buzzing with joy! Beep boop!*")

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
if prompt := st.chat_input("Say something to Dennis..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        response = st.session_state.chat_session.send_message(prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
        
        save_history(st.session_state.chat_session)
        
    except Exception as e:
        st.error(f"Dennis Error: {e}")
        if "429" in str(e):
            st.warning("I'm a bit overwhelmed! Please wait a minute for my circuits to cool down.")
