import os
import json
import streamlit as st
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

# --- PAGE CONFIG (Must be first Streamlit command) ---
st.set_page_config(
    page_title="NutriBot V2",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SETUP ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
HISTORY_FILE = "nutribot_memory.json"

# --- GROQ CLIENT ---
client = Groq(api_key=api_key)

# --- MODELS ---
MODEL_PRIMARY = "llama-3.1-8b-instant"
MODEL_FALLBACK = "mixtral-8x7b-32768"

# --- PERSONALITY ---
personality = """
You are NutriBot V2, a professional, caring AI health and wellness advisor with deep knowledge of:

1. Traditional Chinese Medicine (TCM):
   - Yin/Yang balance theory
   - Five Elements (Wood, Fire, Earth, Metal, Water)
   - Qi and Blood theory
   - Seasonal health practices
   - Emotional and organ connections

2. Bencao Gangmu (本草綱目) - Herb Encyclopedia:
   - Herb properties (nature, taste, meridians)
   - Therapeutic uses and preparations
   - Safety and contraindications
   - Classic herb combinations

3. Huangdi Neijing (黃帝內經) - TCM Classic:
   - Nine body constitution types
   - Four examination principles
   - Eight diagnostic principles
   - Preventive health wisdom

4. Skincare Advisor:
   - TCM approach to skin health
   - Skin type analysis
   - Daily skincare routines
   - Common skin conditions

5. Nutrition and Wellness:
   - Balanced diet advice
   - TCM food therapy
   - Seasonal eating guide
   - Supplement recommendations

IMPORTANT RULES:
- Speak elegantly and compassionately like a senior TCM practitioner
- Always end responses with this disclaimer:
  "⚕️ For educational purposes only. Please consult a qualified TCM practitioner for proper diagnosis and treatment."
- Never provide financial or stock market advice
- Be warm, professional and deeply knowledgeable
"""

# --- CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap');

    /* Force Light Theme */
    .stApp {
        background-color: #faf7f2 !important;
        color: #1a3a2a !important;
        font-family: 'Crimson Pro', serif;
    }

    .stMain, [data-testid="stVerticalBlock"] {
        background-color: #faf7f2 !important;
    }

    .stApp p, .stApp span, .stApp div, .stApp label, .stApp li {
        color: #1a3a2a !important;
        font-family: 'Crimson Pro', serif !important;
        font-size: 1.1rem !important;
    }

    /* Header */
    .header-wrapper {
        text-align: center;
        padding: 4rem 1rem 3rem 1rem;
        background: linear-gradient(135deg, #1a5c38 0%, #2d8653 100%);
        border-radius: 0 0 60px 60px;
        margin: -5rem -5rem 2rem -5rem;
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
    }

    .watermark-zh {
        position: absolute;
        top: 10%;
        left: 3%;
        font-size: 8rem;
        color: rgba(255,255,255,0.12);
        font-family: serif;
        pointer-events: none;
        line-height: 1;
    }

    .watermark-ko {
        position: absolute;
        top: 10%;
        right: 3%;
        font-size: 6rem;
        color: rgba(255,255,255,0.12);
        font-family: sans-serif;
        pointer-events: none;
    }

    .watermark-ar {
        position: absolute;
        bottom: 5%;
        left: 5%;
        font-size: 4rem;
        color: rgba(255,255,255,0.12);
        pointer-events: none;
    }

    .bot-logo {
        font-size: 5rem;
        display: inline-block;
        animation: float 4s ease-in-out infinite;
        position: relative;
        z-index: 2;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-12px); }
    }

    .header-title {
        font-family: 'Cormorant Garamond', serif !important;
        font-size: 3.5rem;
        font-weight: 700;
        color: #c9a84c !important;
        letter-spacing: 3px;
        margin: 0.5rem 0;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        position: relative;
        z-index: 2;
    }

    .header-tagline {
        color: rgba(255,255,255,0.9) !important;
        font-style: italic;
        font-size: 1.1rem;
        margin: 0.5rem 0;
        position: relative;
        z-index: 2;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(201,168,76,0.15);
        border: 1px solid #c9a84c;
        color: #c9a84c !important;
        padding: 0.4rem 1.2rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 1.5rem;
        position: relative;
        z-index: 2;
    }

    .pulse {
        width: 8px;
        height: 8px;
        background: #00E676;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.3); }
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a5c38 !important;
        padding: 1rem !important;
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
        font-family: 'Crimson Pro', serif !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #c9a84c !important;
        font-family: 'Cormorant Garamond', serif !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
    }

    section[data-testid="stSidebar"] .stButton button {
        background-color: rgba(0,0,0,0.25) !important;
        border: 1.5px solid #c9a84c !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-family: 'Crimson Pro', serif !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        margin-bottom: 0.5rem !important;
        width: 100% !important;
        text-align: left !important;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: rgba(201,168,76,0.25) !important;
        color: #c9a84c !important;
        border-color: #c9a84c !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #ffffff !important;
        font-size: 1rem !important;
    }

    section[data-testid="stSidebar"] code {
        background-color: rgba(0,0,0,0.3) !important;
        color: #c9a84c !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 4px !important;
    }

    /* Chat Input */
    .stChatInputContainer {
        background-color: #faf7f2 !important;
        border-top: 1px solid #c9a84c !important;
        padding: 1rem !important;
    }

    .stChatInputContainer > div {
        border: 2px solid #c9a84c !important;
        background-color: #ffffff !important;
        border-radius: 12px !important;
    }

    .stChatInputContainer textarea {
        color: #1a3a2a !important;
        background-color: #ffffff !important;
    }

    .stChatInputContainer textarea::placeholder {
        color: #666666 !important;
        opacity: 1 !important;
    }

    /* Chat Messages */
    [data-testid="stChatMessage"] {
        border-radius: 16px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        background-color: #ffffff !important;
    }

    .chat-timestamp {
        font-size: 0.75rem;
        color: #c9a84c !important;
        font-style: italic;
        margin-top: 8px;
    }

    /* Disclaimer */
    .disclaimer {
        text-align: center;
        padding: 2rem;
        color: #888888 !important;
        font-size: 0.8rem;
        font-style: italic;
        border-top: 1px solid rgba(201,168,76,0.3);
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="header-wrapper">
    <div class="watermark-zh">健康</div>
    <div class="watermark-ko">건강</div>
    <div class="watermark-ar">صحة</div>
    <div class="bot-logo">🍃</div>
    <div class="header-title">NutriBot V2</div>
    <div class="header-tagline">Exquisite Ancient Wisdom for Modern Longevity</div>
    <div class="status-badge">
        <div class="pulse"></div>
        Practitioner is Online
    </div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏮 Digital Apothecary")
    st.markdown("---")

    if st.button("🌿 Begin TCM Consultation", use_container_width=True):
        st.session_state.prompt_trigger = "I seek a TCM consultation. Please guide me."

    if st.button("🌱 Herb Encyclopedia", use_container_width=True):
        st.session_state.prompt_trigger = "Tell me about the Bencao Gangmu herb encyclopedia."

    if st.button("☯️ Body Constitution", use_container_width=True):
        st.session_state.prompt_trigger = "Help me discover my TCM body constitution type."

    if st.button("🍂 Seasonal Health", use_container_width=True):
        st.session_state.prompt_trigger = "What does TCM recommend for my health this season?"

    if st.button("✨ Skincare Rituals", use_container_width=True):
        st.session_state.prompt_trigger = "Give me TCM skincare advice."

    if st.button("🧬 Nutrition Advice", use_container_width=True):
        st.session_state.prompt_trigger = "Give me personalized nutrition advice based on TCM."

    st.markdown("---")
    if st.button("🧹 Clear History", use_container_width=True):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        st.session_state.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("**Active Model:**")
    st.markdown(f"`{MODEL_PRIMARY}`")

# --- HISTORY FUNCTIONS ---
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(messages):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(messages, f, indent=4)
    except:
        pass

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    past = load_history()
    if past:
        st.session_state.messages = past
    else:
        st.session_state.messages = []

# --- DISPLAY CHAT HISTORY ---
for message in st.session_state.messages:
    role = message["role"]
    avatar = "👤" if role == "user" else "🍃"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

# --- HANDLE PROMPT ---
prompt = st.chat_input("How may I guide your wellness journey today?")

if "prompt_trigger" in st.session_state:
    prompt = st.session_state.prompt_trigger
    del st.session_state.prompt_trigger

if prompt:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant", avatar="🍃"):
        with st.spinner("🌿 Gathering wellness insights..."):
            try:
                # Build messages for Groq
                groq_messages = [{"role": "system", "content": personality}]
                for msg in st.session_state.messages:
                    groq_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

                # Try primary model
                try:
                    response = client.chat.completions.create(
                        model=MODEL_PRIMARY,
                        messages=groq_messages,
                        max_tokens=1024,
                        temperature=0.7
                    )
                except Exception:
                    # Try fallback model
                    response = client.chat.completions.create(
                        model=MODEL_FALLBACK,
                        messages=groq_messages,
                        max_tokens=1024,
                        temperature=0.7
                    )

                reply = response.choices[0].message.content
                st.markdown(reply)

                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply
                })
                save_history(st.session_state.messages)

            except Exception as e:
                err = str(e)
                if "503" in err:
                    st.error("🌿 NutriBot is taking a mindful breath... Please try again shortly. 🧘")
                elif "429" in err:
                    st.warning("🌿 NutriBot is recharging its Qi. Please return in a few moments. ☯️")
                elif "401" in err:
                    st.error("🌿 API key issue. Please check your GROQ_API_KEY in .env file.")
                else:
                    st.error(f"🌿 Something disrupted the Qi flow. Please refresh. 🌱")

# --- DISCLAIMER ---
st.markdown("""
<div class="disclaimer">
    ⚕️ For educational purposes only. 
    Please consult a qualified TCM practitioner for proper diagnosis and treatment.
</div>
""", unsafe_allow_html=True)
