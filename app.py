import os
import streamlit as st
from groq import Groq, RateLimitError, InternalServerError, APIStatusError
from dotenv import load_dotenv
import uuid
import json
from firebase_admin import credentials, firestore, initialize_app, get_app

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="NutriBot V2",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FIREBASE SETUP ---
@st.cache_resource
def get_db():
    try:
        try:
            get_app()
        except ValueError:
            # 1. Try Local File FIRST (for local dev)
            if os.path.exists("serviceAccountKey.json"):
                cred = credentials.Certificate("serviceAccountKey.json")
                initialize_app(cred)
            # 2. Try Streamlit Secrets (for cloud dev)
            elif "firebase" in st.secrets:
                key_dict = {
                    "type": st.secrets["firebase"]["type"],
                    "project_id": st.secrets["firebase"]["project_id"],
                    "private_key_id": st.secrets["firebase"]["private_key_id"],
                    "private_key": st.secrets["firebase"]["private_key"],
                    "client_email": st.secrets["firebase"]["client_email"],
                    "client_id": st.secrets["firebase"]["client_id"],
                    "auth_uri": st.secrets["firebase"]["auth_uri"],
                    "token_uri": st.secrets["firebase"]["token_uri"],
                    "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
                    "universe_domain": "googleapis.com"
                }
                cred = credentials.Certificate(key_dict)
                initialize_app(cred)
            else:
                return None, "Missing Credentials (serviceAccountKey.json not found)"
        
        return firestore.client(), "Success"
    except Exception as e:
        return None, str(e)

db, db_status = get_db()

if db:
    st.sidebar.success("✅ Database Connected")
else:
    st.sidebar.error(f"❌ Database Error: {db_status}")

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

import time

# --- LOGGING FUNCTIONS ---
def detect_category(text):
    text = text.lower()
    keywords = {
        "Skincare": ["skin", "acne", "complexion", "glow", "dermatology", "ritual"],
        "TCM": ["qi", "meridians", "yin", "yang", "tongue", "pulse", "herbs", "bencao", "huangdi"],
        "Nutrition": ["diet", "food", "protein", "vitamin", "calories", "eating", "recipe"],
        "Wellness": ["stress", "sleep", "meditation", "mental", "anxiety", "constitution"],
        "Fitness": ["workout", "exercise", "gym", "muscle", "cardio", "activity"]
    }
    for category, tags in keywords.items():
        if any(tag in text for tag in tags):
            return category
    return "General"

def log_question(question):
    if db:
        try:
            category = detect_category(question)
            db.collection("nutribot_logs").add({
                "question": question,
                "category": category,
                "session_id": st.session_state.session_id,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.sidebar.write("📝 Question Logged")
        except Exception as e:
            st.sidebar.error(f"Log Error: {e}")
    else:
        st.sidebar.error("❌ Database Not Initialized")

def log_interaction(event_type, data):
    if db:
        try:
            doc_data = {
                "event_type": event_type,
                "session_id": st.session_state.session_id,
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            doc_data.update(data)
            db.collection("nutribot_metrics").add(doc_data)
            st.sidebar.write(f"📊 {event_type} Logged")
        except Exception as e:
            st.sidebar.error(f"Metric Error: {e}")
    else:
        st.sidebar.error("❌ Database Not Initialized")

# --- 20s ENGAGEMENT WINDOW ---
def engagement_window():
    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()
    
    elapsed = time.time() - st.session_state.start_time
    
    # Show interaction between 10s and 30s of the session (20s window)
    if 10 <= elapsed <= 30 and "engagement_answered" not in st.session_state:
        with st.container():
            st.markdown("""
                <div style="background-color: #c9a84c; padding: 15px; border-radius: 12px; border-left: 6px solid #1a5c38; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <p style="color: #1a5c38; margin: 0; font-weight: bold; font-size: 1.1rem;">🏮 Quick Pulse: What is your primary wellness goal today?</p>
                    <p style="color: #1a5c38; font-size: 0.85rem; margin-top: 5px; font-style: italic;">Help us tailor your experience in 1 click.</p>
                </div>
            """, unsafe_allow_html=True)
            
            cols = st.columns(4)
            if cols[0].button("💆 Stress", use_container_width=True):
                st.session_state.engagement_answered = "Stress Relief"
                log_interaction("goal_selection", {"goal": "Stress Relief"})
                st.rerun()
            if cols[1].button("✨ Skin", use_container_width=True):
                st.session_state.engagement_answered = "Better Skin"
                log_interaction("goal_selection", {"goal": "Better Skin"})
                st.rerun()
            if cols[2].button("🔋 Energy", use_container_width=True):
                st.session_state.engagement_answered = "More Energy"
                log_interaction("goal_selection", {"goal": "More Energy"})
                st.rerun()
            if cols[3].button("🍎 Diet", use_container_width=True):
                st.session_state.engagement_answered = "Better Diet"
                log_interaction("goal_selection", {"goal": "Better Diet"})
                st.rerun()

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;700&family=Crimson+Pro:wght@300;400;600&display=swap');

.stApp { background-color: #faf7f2 !important; }
.stMain, [data-testid="stVerticalBlock"] { background-color: #faf7f2 !important; }

section[data-testid="stSidebar"] { background-color: #1a5c38 !important; }
section[data-testid="stSidebar"] > div { background-color: #1a5c38 !important; }
section[data-testid="stSidebar"] p { color: #ffffff !important; font-size: 1.05rem !important; font-weight: 500 !important; opacity: 1 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #c9a84c !important; font-size: 1.4rem !important; font-weight: 700 !important; opacity: 1 !important; }
section[data-testid="stSidebar"] span { color: #ffffff !important; font-weight: 500 !important; opacity: 1 !important; }
section[data-testid="stSidebar"] label { color: #ffffff !important; font-weight: 500 !important; opacity: 1 !important; }
section[data-testid="stSidebar"] .stButton > button {
    background-color: #2d8653 !important;
    border: 2px solid #c9a84c !important;
    color: #ffffff !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0.6rem 1rem !important;
    margin-bottom: 8px !important;
    width: 100% !important;
    opacity: 1 !important;
    visibility: visible !important;
}
section[data-testid="stSidebar"] .stButton > button p {
    color: #ffffff !important;
    opacity: 1 !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #c9a84c !important;
    color: #1a5c38 !important;
    border: 2px solid #ffffff !important;
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
logo_base64 = "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) "
header_html = f"""<div style="background:linear-gradient(135deg,#1a5c38 0%,#2d8653 100%);border-radius:0 0 60px 60px;margin-bottom:2rem;box-shadow:0 15px 40px rgba(0,0,0,0.15);position:relative;height:450px;width:100%;overflow:hidden;"><span style="position:absolute;top:10px;left:10px;font-size:160px;color:rgba(255,255,255,0.2);font-family:serif;line-height:1;display:block;">健康</span><span style="position:absolute;top:10px;right:10px;font-size:140px;color:rgba(255,255,255,0.2);font-family:sans-serif;line-height:1;display:block;text-align:right;">건강</span><span style="position:absolute;bottom:10px;left:10px;font-size:90px;color:rgba(255,255,255,0.2);line-height:1;display:block;">صحة</span><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;z-index:10;width:100%;"><div style="margin-bottom:1rem;"><img src="data:image/png;base64,{{logo_base64}}" width="120" style="filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));"></div><div style="font-size:3.5rem;margin-bottom:0.3rem;">🍃</div><div style="font-family:Georgia,serif;font-size:2.8rem;font-weight:700;color:#c9a84c;letter-spacing:3px;text-shadow:1px 1px 3px rgba(0,0,0,0.3);">NutriBot V2</div><div style="color:rgba(255,255,255,0.9);font-style:italic;font-size:1rem;margin:0.4rem 0;">Exquisite Ancient Wisdom for Modern Longevity</div><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(201,168,76,0.2);border:1px solid #c9a84c;color:#c9a84c;padding:0.3rem 1.2rem;border-radius:50px;font-size:0.85rem;font-weight:600;margin-top:0.8rem;"><span style="color:#00E676;">●</span> Practitioner is Online</div></div></div>"""
header_html = header_html.format(logo_base64=logo_base64)
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
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- DISPLAY HISTORY ---
for message in st.session_state.messages:
    role = message["role"]
    avatar = "👤" if role == "user" else "🍃"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

# --- ENGAGEMENT WINDOW ---
engagement_window()

# --- CHAT INPUT ---
prompt = st.chat_input("How may I guide your wellness journey today?")

if "prompt_trigger" in st.session_state:
    prompt = st.session_state.prompt_trigger
    del st.session_state.prompt_trigger

if prompt:
    log_question(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🍃"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Prepare messages (Limit to last 10 to save tokens/context)
            groq_messages = [{"role": "system", "content": personality}]
            for msg in st.session_state.messages[-10:]:
                groq_messages.append({"role": msg["role"], "content": msg["content"]})
            
            try:
                completion = client.chat.completions.create(
                    model=MODEL_PRIMARY, 
                    messages=groq_messages, 
                    max_tokens=1024, 
                    temperature=0.7,
                    stream=True
                )
            except Exception:
                completion = client.chat.completions.create(
                    model=MODEL_FALLBACK, 
                    messages=groq_messages, 
                    max_tokens=1024, 
                    temperature=0.7,
                    stream=True
                )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except RateLimitError:
            st.warning("🌿 NutriBot is recharging its Qi. Please return in a few moments. ☯️")
        except (InternalServerError, APIStatusError):
            st.error("🌿 NutriBot is taking a mindful breath... Please try again shortly. 🧘")
        except Exception as e:
            st.error("🌿 Something disrupted the Qi flow. Please refresh. 🌱")

# --- DISCLAIMER ---
st.markdown('<div style="text-align:center;padding:2rem;color:#888888;font-size:0.85rem;font-style:italic;border-top:1px solid rgba(201,168,76,0.3);margin-top:2rem;">⚕️ For educational purposes only. Please consult a qualified TCM practitioner for proper diagnosis and treatment.</div>', unsafe_allow_html=True)
