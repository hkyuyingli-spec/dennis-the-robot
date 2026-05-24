import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="NutriBot V2",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SETUP ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)
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

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;700&family=Crimson+Pro:wght@300;400;600&display=swap');

.stApp { background-color: #faf7f2 !important; }
.stMain, [data-testid="stVerticalBlock"] { background-color: #faf7f2 !important; }

section[data-testid="stSidebar"] { background-color: #1a5c38 !important; }
section[data-testid="stSidebar"] > div { background-color: #1a5c38 !important; }
section[data-testid="stSidebar"] p { color: #ffffff !important; font-size: 1rem !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #c9a84c !important; font-size: 1.3rem !important; font-weight: 700 !important; }
section[data-testid="stSidebar"] span { color: #ffffff !important; }
section[data-testid="stSidebar"] label { color: #ffffff !important; }
section[data-testid="stSidebar"] .stButton > button {
    background-color: rgba(255,255,255,0.15) !important;
    border: 1.5px solid #c9a84c !important;
    color: #000000 !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    margin-bottom: 6px !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #c9a84c !important;
    color: #1a3a2a !important;
}
section[data-testid="stSidebar"] code {
    background-color: rgba(0,0,0,0.4) !important;
    color: #c9a84c !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
}

.stChatInputContainer { background-color: #faf7f2 !important; border-top: 2px solid #c9a84c !important; }
.stChatInputContainer > div { border: 2px solid #c9a84c !important; background-color: #ffffff !important; border-radius: 12px !important; }
.stChatInputContainer textarea { color: #1a3a2a !important; background-color: #ffffff !important; font-size: 1rem !important; }
.stChatInputContainer textarea::placeholder { color: #888888 !important; opacity: 1 !important; }

[data-testid="stChatMessage"] { border-radius: 16px !important; padding: 1rem !important; margin-bottom: 1rem !important; background-color: #ffffff !important; }

.stMarkdown p { color: #1a3a2a !important; font-family: 'Crimson Pro', serif !important; font-size: 1.1rem !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
header_html = """<div style="background:linear-gradient(135deg,#1a5c38 0%,#2d8653 100%);border-radius:0 0 60px 60px;margin-bottom:2rem;box-shadow:0 15px 40px rgba(0,0,0,0.15);position:relative;height:380px;width:100%;overflow:hidden;"><span style="position:absolute;top:10px;left:10px;font-size:160px;color:rgba(255,255,255,0.2);font-family:serif;line-height:1;display:block;">健康</span><span style="position:absolute;top:10px;right:10px;font-size:140px;color:rgba(255,255,255,0.2);font-family:sans-serif;line-height:1;display:block;text-align:right;">건강</span><span style="position:absolute;bottom:10px;left:10px;font-size:90px;color:rgba(255,255,255,0.2);line-height:1;display:block;">صحة</span><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;z-index:10;width:100%;"><div style="font-size:3.5rem;margin-bottom:0.3rem;">🍃</div><div style="font-family:Georgia,serif;font-size:2.8rem;font-weight:700;color:#c9a84c;letter-spacing:3px;text-shadow:1px 1px 3px rgba(0,0,0,0.3);">NutriBot V2</div><div style="color:rgba(255,255,255,0.9);font-style:italic;font-size:1rem;margin:0.4rem 0;">Exquisite Ancient Wisdom for Modern Longevity</div><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(201,168,76,0.2);border:1px solid #c9a84c;color:#c9a84c;padding:0.3rem 1.2rem;border-radius:50px;font-size:0.85rem;font-weight:600;margin-top:0.8rem;"><span style="color:#00E676;">●</span> Practitioner is Online</div></div></div>"""
st.markdown(header_html, unsafe_allow_html=True)

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
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    st.markdown("**Active Model:**")
    st.markdown(f"`{MODEL_PRIMARY}`")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- DISPLAY HISTORY ---
for message in st.session_state.messages:
    role = message["role"]
    avatar = "👤" if role == "user" else "🍃"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

# --- CHAT INPUT ---
prompt = st.chat_input("How may I guide your wellness journey today?")

if "prompt_trigger" in st.session_state:
    prompt = st.session_state.prompt_trigger
    del st.session_state.prompt_trigger

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🍃"):
        with st.spinner("🌿 Gathering wellness insights..."):
            try:
                groq_messages = [{"role": "system", "content": personality}]
                for msg in st.session_state.messages:
                    groq_messages.append({"role": msg["role"], "content": msg["content"]})
                try:
                    response = client.chat.completions.create(model=MODEL_PRIMARY, messages=groq_messages, max_tokens=1024, temperature=0.7)
                except Exception:
                    response = client.chat.completions.create(model=MODEL_FALLBACK, messages=groq_messages, max_tokens=1024, temperature=0.7)
                reply = response.choices[0].message.content
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                err = str(e)
                if "503" in err:
                    st.error("🌿 NutriBot is taking a mindful breath... Please try again shortly. 🧘")
                elif "429" in err:
                    st.warning("🌿 NutriBot is recharging its Qi. Please return in a few moments. ☯️")
                elif "401" in err:
                    st.error("🌿 API key issue. Please check your GROQ_API_KEY.")
                else:
                    st.error("🌿 Something disrupted the Qi flow. Please refresh. 🌱")

# --- DISCLAIMER ---
st.markdown('<div style="text-align:center;padding:2rem;color:#888888;font-size:0.85rem;font-style:italic;border-top:1px solid rgba(201,168,76,0.3);margin-top:2rem;">⚕️ For educational purposes only. Please consult a qualified TCM practitioner for proper diagnosis and treatment.</div>', unsafe_allow_html=True)
