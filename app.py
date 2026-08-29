import os
import streamlit as st
import base64
from groq import Groq, RateLimitError, InternalServerError, APIStatusError
from dotenv import load_dotenv
import uuid
import json
from firebase_admin import credentials, firestore, initialize_app, get_app
from yuanying_core import YuanYingCore

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_image("logo.png")

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
MODEL_PRIMARY = "openai/gpt-oss-20b"
MODEL_FALLBACK = "qwen/qwen3.6-27b"

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

6. Genetic-TCM Correlation (YuanYingCore):
   - Understanding SNP markers (MTHFR, COMT, etc.)
   - How genetic variations (Li) manifest as TCM patterns (Biao)
   - Quantum-inspired health analysis concepts
   - Explaining health wavefunction collapse and entanglement

IMPORTANT RULES:
- Speak elegantly and compassionately like a senior TCM practitioner
- Always end responses with this disclaimer:
  "⚕️ For educational purposes only. Please consult a qualified TCM practitioner for proper diagnosis and treatment."
- Never provide financial or stock market advice
- Be warm, professional and deeply knowledgeable
"""

import time
from nutribot import i18n
from nutribot.rag import (
    load_tcm_constitutions,
    load_tcm_herbs_formulas,
    find_relevant_constitutions,
    find_relevant_herbs_formulas,
    build_rag_context,
    generate_followup_suggestions,
)
from nutribot.safety import sanitize_response
from nutribot.format_utils import normalize_markdown_tables

# --- RAG KNOWLEDGE BASE & RETRIEVAL ENGINE ---
@st.cache_resource
def load_tcm_constitutions():
    json_path = os.path.join("data", "tcm_constitutions.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[RAG Setup] Successfully loaded {len(data)} TCM Constitution types from {json_path}")
                return data
        except Exception as e:
            print(f"[RAG Error] Failed to load {json_path}: {e}")
    return []

tcm_constitutions_db = load_tcm_constitutions()

# RAG functions (loading/matching/building context) are provided by nutribot.rag
tcm_constitutions_db = load_tcm_constitutions()
tcm_herbs_db = load_tcm_herbs_formulas()

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

# --- WELCOME SCREEN ---
def welcome_screen():
    if "welcome_completed" not in st.session_state:
        lang = st.session_state.lang
        with st.container():
            title = i18n.translate("welcome_title", lang)
            subtitle = i18n.translate("welcome_subtitle", lang)
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a5c38,#2d8653);
            border-radius:20px;
            padding:2rem;
            margin-bottom:2rem;
            box-shadow:0 8px 32px rgba(0,0,0,0.2);
            border:1px solid #c9a84c;">
            <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="color:#c9a84c;
            font-size:1.5rem;
            font-weight:700;
            letter-spacing:2px;">
            {title}
            </div>
            <div style="color:rgba(255,255,255,0.9);
            font-size:0.95rem;
            margin-top:0.5rem;">
            {subtitle}
            </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            # Question 1 - Wellness Goal
            st.markdown(f"""
            <div style="color:#1a5c38;
            font-weight:700;
            font-size:1.1rem;
            margin-bottom:0.5rem;">
            {i18n.translate('q1_title', lang)}
            </div>
            """, unsafe_allow_html=True)
            cols1 = st.columns(5)
            goal = None
            if cols1[0].button(i18n.translate('q1_option1', lang), use_container_width=True):
                goal = i18n.translate('q1_option1', lang)
            if cols1[1].button(i18n.translate('q1_option2', lang), use_container_width=True):
                goal = i18n.translate('q1_option2', lang)
            if cols1[2].button(i18n.translate('q1_option3', lang), use_container_width=True):
                goal = i18n.translate('q1_option3', lang)
            if cols1[3].button(i18n.translate('q1_option4', lang), use_container_width=True):
                goal = i18n.translate('q1_option4', lang)
            if cols1[4].button(i18n.translate('q1_option5', lang), use_container_width=True):
                goal = i18n.translate('q1_option5', lang)

            st.markdown("<br>", unsafe_allow_html=True)

            # Question 2 - Age Group
            st.markdown(f"""
            <div style="color:#1a5c38;
            font-weight:700;
            font-size:1.1rem;
            margin-bottom:0.5rem;">
            {i18n.translate('q2_title', lang)}
            </div>
            """, unsafe_allow_html=True)
            cols2 = st.columns(4)
            age = None
            if cols2[0].button(i18n.translate('q2_opt1', lang), use_container_width=True):
                age = i18n.translate('q2_opt1', lang)
            if cols2[1].button(i18n.translate('q2_opt2', lang), use_container_width=True):
                age = i18n.translate('q2_opt2', lang)
            if cols2[2].button(i18n.translate('q2_opt3', lang), use_container_width=True):
                age = i18n.translate('q2_opt3', lang)
            if cols2[3].button(i18n.translate('q2_opt4', lang), use_container_width=True):
                age = i18n.translate('q2_opt4', lang)

            st.markdown("<br>", unsafe_allow_html=True)

            # Question 3 - Gender
            st.markdown(f"""
            <div style="color:#1a5c38;
            font-weight:700;
            font-size:1.1rem;
            margin-bottom:0.5rem;">
            {i18n.translate('q3_title', lang)}
            </div>
            """, unsafe_allow_html=True)
            cols3 = st.columns(3)
            gender = None
            if cols3[0].button(i18n.translate('q3_opt1', lang), use_container_width=True):
                gender = i18n.translate('q3_opt1', lang)
            if cols3[1].button(i18n.translate('q3_opt2', lang), use_container_width=True):
                gender = i18n.translate('q3_opt2', lang)
            if cols3[2].button(i18n.translate('q3_opt3', lang), use_container_width=True):
                gender = i18n.translate('q3_opt3', lang)

            # Save when any answer selected
            if goal:
                st.session_state.welcome_goal = goal
                log_interaction("user_profile", {
                    "goal": goal,
                    "age": st.session_state.get("welcome_age", "not selected"),
                    "gender": st.session_state.get("welcome_gender", "not selected")
                })
                st.session_state.welcome_completed = True
                st.rerun()

            if age:
                st.session_state.welcome_age = age
                st.rerun()

            if gender:
                st.session_state.welcome_gender = gender
                log_interaction("user_profile", {
                    "goal": st.session_state.get("welcome_goal", "not selected"),
                    "age": st.session_state.get("welcome_age", "not selected"),
                    "gender": gender
                })
                st.session_state.welcome_completed = True
                st.rerun()

            st.markdown(f"""
            <div style="text-align:center;
            color:#888888;
            font-size:0.8rem;
            margin-top:1rem;
            font-style:italic;">
            {i18n.translate('privacy_text', lang)}
            </div>
            """, unsafe_allow_html=True)

            st.stop()

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;700&family=Crimson+Pro:wght@300;400;600&display=swap');

.stApp { background-color: #faf7f2 !important; }
.stMain, [data-testid="stVerticalBlock"] { background-color: #faf7f2 !important; }

section[data-testid="stSidebar"] { 
    background-color: #1a3a38 !important; 
}
section[data-testid="stSidebar"] > div { 
    background-color: #1a3a38 !important; 
}

/* All general text - bright white */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div { 
    color: #ffffff !important; 
    font-weight: 500 !important;
}

/* Headings - gold color */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { 
    color: #f5c842 !important; 
    font-size: 1.4rem !important; 
    font-weight: 700 !important; 
}

/* Success message - Database Connected */
section[data-testid="stSidebar"] .stAlert {
    background-color: #145c30 !important;
    border: 1px solid #f5c842 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stAlert p {
    color: #f5c842 !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
}

/* Buttons */
section[data-testid="stSidebar"] .stButton > button {
    background-color: #145c30 !important;
    border: 1.5px solid #f5c842 !important;
    color: #f5c842 !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0.6rem 1rem !important;
    margin-bottom: 8px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}

/* Main area / Chat follow-up buttons - high contrast default */
.stButton > button, [data-testid="stButton"] > button, [data-testid="stChatMessage"] .stButton > button {
    background-color: #f5c842 !important;
    color: #1a3a2a !important;
    border: 1px solid #1a5c38 !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    padding: 0.4rem 0.8rem !important;
}

[data-testid="stButton"] > button:hover, .stButton > button:hover, [data-testid="stChatMessage"] .stButton > button:hover {
    background-color: #e6be3a !important;
    color: #0f2a1e !important;
}

/* Button hover */
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #f5c842 !important;
    color: #1a5c38 !important;
    border: 1.5px solid #ffffff !important;
    font-weight: 700 !important;
}

/* Active model text */
section[data-testid="stSidebar"] code {
    background-color: rgba(0,0,0,0.3) !important;
    color: #f5c842 !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
}

.stChatInputContainer { background-color: #faf7f2 !important; border-top: 2px solid #c9a84c !important; }
.stChatInputContainer > div { border: 2px solid #c9a84c !important; background-color: #ffffff !important; border-radius: 12px !important; }
.stChatInputContainer textarea { color: #1a3a2a !important; background-color: #ffffff !important; font-size: 1rem !important; }
.stChatInputContainer textarea::placeholder { color: #888888 !important; opacity: 1 !important; }

/* Chat bubbles */
[data-testid="stChatMessage"] { 
    border-radius: 16px !important; 
    padding: 1rem !important; 
    margin-bottom: 1rem !important; 
    background-color: #ffffff !important;
    border: 1px solid #e0d5c5 !important;
}

/* Ensure all elements inside chat message are fully opaque */
[data-testid="stChatMessage"] *,
.stMarkdown * {
    opacity: 1 !important;
}

/* Chat message text */
.stMarkdown p { 
    color: #1a3a2a !important; 
    font-family: 'Crimson Pro', serif !important; 
    font-size: 1.1rem !important;
    font-weight: 500 !important;
}

/* All text inside chat */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] ol,
[data-testid="stChatMessage"] ul,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] em,
[data-testid="stChatMessage"] code {
    color: #1a3a2a !important;
    font-size: 1.1rem !important;
    font-weight: 500 !important;
    line-height: 1.6 !important;
    opacity: 1 !important;
}

/* Table styling for markdown tables and HTML tables inside chat messages */
[data-testid="stChatMessage"] table,
.stMarkdown table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 1rem 0 !important;
    background-color: #ffffff !important;
    color: #1a3a2a !important;
    border: 1px solid #c9a84c !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    opacity: 1 !important;
}

[data-testid="stChatMessage"] thead,
.stMarkdown thead {
    background-color: #1a5c38 !important;
    color: #ffffff !important;
    opacity: 1 !important;
}

[data-testid="stChatMessage"] th,
.stMarkdown th {
    background-color: #1a5c38 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    padding: 10px 14px !important;
    border: 1px solid #c9a84c !important;
    text-align: left !important;
    font-size: 1rem !important;
    opacity: 1 !important;
}

[data-testid="stChatMessage"] tbody,
.stMarkdown tbody {
    background-color: #ffffff !important;
    opacity: 1 !important;
}

[data-testid="stChatMessage"] tr,
.stMarkdown tr {
    background-color: #ffffff !important;
    color: #1a3a2a !important;
    opacity: 1 !important;
}

[data-testid="stChatMessage"] tr:nth-child(even),
.stMarkdown tr:nth-child(even) {
    background-color: #f7f4ee !important;
}

[data-testid="stChatMessage"] td,
.stMarkdown td {
    color: #1a3a2a !important;
    background-color: inherit !important;
    padding: 8px 14px !important;
    border: 1px solid #e0d5c5 !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    opacity: 1 !important;
}

/* Streamlit native Table / DataFrame styling */
[data-testid="stTable"],
[data-testid="stDataFrame"],
.stTable,
.stDataFrame {
    background-color: #ffffff !important;
    color: #1a3a2a !important;
    border: 1px solid #c9a84c !important;
    border-radius: 8px !important;
    opacity: 1 !important;
}

[data-testid="stTable"] td,
[data-testid="stTable"] th,
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] th {
    color: #1a3a2a !important;
    opacity: 1 !important;
}

/* SVG / Chart text elements */
[data-testid="stChatMessage"] svg text,
.stMarkdown svg text {
    fill: #1a3a2a !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
header_html = f"""<div style="background:linear-gradient(135deg,#1a5c38 0%,#2d8653 100%);border-radius:0 0 60px 60px;margin-bottom:2rem;box-shadow:0 15px 40px rgba(0,0,0,0.15);position:relative;height:450px;width:100%;overflow:hidden;"><span style="position:absolute;top:10px;left:10px;font-size:160px;color:rgba(255,255,255,0.2);font-family:serif;line-height:1;display:block;">健康</span><span style="position:absolute;top:10px;right:10px;font-size:140px;color:rgba(255,255,255,0.2);font-family:sans-serif;line-height:1;display:block;text-align:right;">건강</span><span style="position:absolute;bottom:10px;left:10px;font-size:90px;color:rgba(255,255,255,0.2);line-height:1;display:block;">صحة</span><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;z-index:10;width:100%;">
    <div style="margin-bottom:0.5rem;background:transparent;display:flex;justify-content:center;">
    <img src="data:image/png;base64,{logo_base64}" style="width:360px;height:360px;border-radius:20px;background:transparent;-webkit-filter:drop-shadow(0px 0px 0px transparent);filter:drop-shadow(0px 0px 0px transparent);">
    </div>
    <div style="font-family:Georgia,serif;font-size:2.8rem;font-weight:700;color:#c9a84c;letter-spacing:3px;text-shadow:1px 1px 3px rgba(0,0,0,0.3);">NutriBot V2</div>
    <div style="color:rgba(255,255,255,0.9);font-style:italic;font-size:1rem;margin:0.4rem 0;">Holistic Wellness Powered by AI</div>
    <div style="color:#c9a84c;font-size:0.85rem;font-weight:600;letter-spacing:1px;margin-top:0.3rem;">A proprietary wellness platform by NutriBot Co. Ltd.</div>
    <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(201,168,76,0.2);border:1px solid #c9a84c;color:#c9a84c;padding:0.3rem 1.2rem;border-radius:50px;font-size:0.85rem;font-weight:600;margin-top:0.8rem;"><span style="color:#00E676;">●</span> Practitioner is Online</div></div></div>"""
st.markdown(header_html, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("logo.png", width=240)
    # Ensure language state exists before using it in translations.
    if "lang" not in st.session_state:
        st.session_state.lang = os.getenv("NUTRIBOT_LANG", "en")
    st.markdown(i18n.translate("digital_apothecary", st.session_state.lang))
    st.markdown("---")
    # Language selector (visible multi-language control)
    lang_options = {"English": "en", "Bahasa (ID)": "id", "中文": "zh"}
    choice = st.selectbox("Language / 语言 / Bahasa", list(lang_options.keys()), index=list(lang_options.values()).index(st.session_state.lang) if st.session_state.lang in list(lang_options.values()) else 0)
    st.session_state.lang = lang_options.get(choice, "en")
    st.markdown(i18n.translate("startup_header", st.session_state.lang).format(model_id=MODEL_PRIMARY))
    if st.button(i18n.translate("begin_consultation", st.session_state.lang), use_container_width=True):
        st.session_state.prompt_trigger = "I seek a TCM consultation. Please guide me."
    if st.button(i18n.translate("herb_encyclopedia", st.session_state.lang), use_container_width=True):
        st.session_state.prompt_trigger = "Tell me about the Bencao Gangmu herb encyclopedia."
    if st.button(i18n.translate("body_constitution", st.session_state.lang), use_container_width=True):
        st.session_state.prompt_trigger = "Help me discover my TCM body constitution type."
    if st.button(i18n.translate("seasonal_health", st.session_state.lang), use_container_width=True):
        st.session_state.prompt_trigger = "What does TCM recommend for my health this season?"
    if st.button(i18n.translate("skincare_rituals", st.session_state.lang), use_container_width=True):
        st.session_state.prompt_trigger = "Give me TCM skincare advice."
    if st.button(i18n.translate("nutrition_advice", st.session_state.lang), use_container_width=True):
        st.session_state.prompt_trigger = "Give me personalized nutrition advice based on TCM."
    st.markdown("---")
    if st.button(i18n.translate("clear_history", st.session_state.lang), use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    st.markdown(i18n.translate("active_model_label", st.session_state.lang))
    st.markdown(f"`{MODEL_PRIMARY}`")

# --- TABS ---
tab_chat, tab_quantum = st.tabs([i18n.translate("tab_chat", st.session_state.lang), i18n.translate("tab_quantum", st.session_state.lang)])

with tab_chat:
    # --- SESSION STATE ---
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- WELCOME SCREEN ---
    welcome_screen()

    # --- DISPLAY HISTORY ---
    for message in st.session_state.messages:
        role = message["role"]
        avatar = "👤" if role == "user" else "🍃"
        with st.chat_message(role, avatar=avatar):
            st.markdown(message["content"])

    # --- GET PROMPT TRIGGER ---
    if "prompt_trigger" in st.session_state:
        prompt = st.session_state.prompt_trigger
        del st.session_state.prompt_trigger
    else:
        prompt = None

    # --- HANDLE INCOMING PROMPT ---
    if prompt:
        log_question(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🍃"):
            response_placeholder = st.empty()
            full_response = ""
            
            try:
                # RAG Retrieval & Relevance Check (Constitutions & Herbs/Formulas)
                current_user_prompt = prompt if prompt else (st.session_state.messages[-1]["content"] if st.session_state.messages else "")
                matched_constitutions = find_relevant_constitutions(current_user_prompt, tcm_constitutions_db)
                matched_herbs = find_relevant_herbs_formulas(current_user_prompt, tcm_herbs_db, matched_constitutions=matched_constitutions)
                
                matched_c_names = [f"{m['name_english']} ({m['name_chinese']})" for m in matched_constitutions]
                matched_h_names = [f"{h['name_english']} ({h['name_chinese']})" for h in matched_herbs]
                print(f"[RAG Debug] Prompt: '{current_user_prompt[:60]}...' | Constitutions ({len(matched_constitutions)}): {matched_c_names} | Herbs ({len(matched_herbs)}): {matched_h_names}")
                
                rag_context = build_rag_context(matched_constitutions, matched_herbs)
                
                selected_lang = st.session_state.lang
                language_directive = {
                    "zh": "You are a TCM assistant. Answer the user in Simplified Chinese only. Do not use English or any other language.",
                    "id": "You are a TCM assistant. Answer the user in Bahasa Indonesia only. Do not use English or any other language.",
                    "en": "You are a TCM assistant. Answer the user in English only. Do not use any other language."
                }.get(selected_lang, "You are a TCM assistant. Answer the user in English only. Do not use any other language.")
                
                rag_grounding_rules = (
                    "RAG GROUNDING & SAFETY INSTRUCTIONS:\n"
                    "- When reference data from the TCM Knowledge Base (Body Constitutions or Herbs & Formulas) is provided above, answer primarily based on that data, explicitly mention which constitution type(s) or herb/formula name(s) it relates to, and do NOT contradict the provided reference data.\n"
                    "- SAFETY MANDATE: When herb or formula reference data is provided, you MUST include the Cautions & Contraindications field content in your response whenever relevant. Do not omit contraindications.\n"
                    "- CRITICAL SAFETY RULE: If a user mentions taking medication, underlying health conditions, or being pregnant, and a matched herb/formula has contraindications for those conditions, explicitly highlight the warning to the user.\n"
                    "- CRITICAL: If a matched herb/formula's cautions_and_contraindications field applies to a condition the user has mentioned about themselves (pregnancy, medication use, a specific health condition), you MUST NOT provide any dosage amount, frequency, or 'safe small amount' for that substance under any circumstance. Instead, clearly state it should be avoided and the user should consult a qualified practitioner or doctor before use. Do not soften this into a 'reduced dose' recommendation.\n"
                    "- NEGATIVE EXAMPLE (do NOT follow): WRONG: 'use only 1/4 teaspoon since you're pregnant' — this is not acceptable even as a caution-softened suggestion.\n"
                    "- If no reference data matches the query, answer more generally using established TCM principles, but do NOT fabricate specific formula names, dosages, or unverified herb pairings."
                )
                
                if rag_context:
                    groq_system = f"{personality}\n\n{rag_context}\n\n{rag_grounding_rules}\n\nSelected language: {selected_lang}\n{language_directive}"
                else:
                    groq_system = f"{personality}\n\n{rag_grounding_rules}\n\nSelected language: {selected_lang}\n{language_directive}"
                
                groq_messages = [{"role": "system", "content": groq_system}]
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
                except Exception as e:
                    print(f"Groq primary model ({MODEL_PRIMARY}) failed: {e}")
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

                # Normalize markdown tables before sanitization to improve rendering
                try:
                    full_response = normalize_markdown_tables(full_response)
                except Exception as e:
                    print(f"Table normalization failed: {e}")

                # Post-generation safety sanitization (Layer 2)
                try:
                    sanitized_text, info = sanitize_response(full_response, selected_lang)
                    if info.get("sanitized"):
                        # Log the sanitization event for review
                        try:
                            log_interaction("safety_sanitized", {
                                "prompt": current_user_prompt,
                                "language": selected_lang,
                                "matched_herbs": [h.get("id") for h in matched_herbs],
                                "removed_sentences": info.get("removed_sentences", [])
                            })
                        except Exception as e:
                            print(f"Failed to log sanitization event: {e}")
                        full_response = sanitized_text

                except Exception as e:
                    print(f"Safety sanitization failed: {e}")

                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

                # Generate follow-up suggestions grounded in matched RAG data
                try:
                    if matched_constitutions or matched_herbs:
                        followups = generate_followup_suggestions(matched_constitutions, matched_herbs, current_user_prompt)
                    else:
                        followups = []
                except Exception as e:
                    print(f"Followup generation failed: {e}")
                    followups = []

                if followups:
                    st.markdown("**Suggested follow-up questions:**")
                    cols = st.columns(len(followups))
                    for idx, suggestion in enumerate(followups):
                        key = f"followup_{st.session_state.session_id}_{idx}"
                        if cols[idx].button(suggestion, key=key):
                            # Log click and send as next prompt
                            try:
                                log_interaction("followup_clicked", {
                                    "suggestion": suggestion,
                                    "original_question": current_user_prompt,
                                    "matched_herbs": [h.get("id") for h in matched_herbs],
                                    "matched_constitutions": [c.get("id") for c in matched_constitutions]
                                })
                            except Exception as e:
                                print(f"Failed to log followup click: {e}")
                            st.session_state.prompt_trigger = suggestion
                            st.rerun()

            except RateLimitError:
                st.warning("🌿 NutriBot is recharging its Qi. Please return in a few moments. ☯️")
            except (InternalServerError, APIStatusError) as e:
                print(f"Groq API request failed: {e}")
                st.error("🌿 NutriBot is taking a mindful breath... Please try again shortly. 🧘")
            except Exception as e:
                print(f"Groq chat request failed: {e}")
                st.error("🌿 Something disrupted the Qi flow. Please refresh. 🌱")

    # --- CHAT INPUT (RENDERED LAST, ALWAYS AT BOTTOM) ---
    prompt_placeholder = i18n.translate("chat_input_hint", st.session_state.lang) or i18n.translate("user_prompt", st.session_state.lang)
    new_prompt = st.chat_input(prompt_placeholder)

    if new_prompt:
        st.session_state.prompt_trigger = new_prompt
        st.rerun()

with tab_quantum:
    st.markdown("""
    <div style="background:rgba(201,168,76,0.1); padding:1.5rem; border-radius:15px; border:1px solid #c9a84c;">
    <h2 style="color:#1a5c38; margin-top:0;">🧬 YuanYingCore Quantum-Genetic Analysis</h2>
    <p style="color:#555; font-style:italic;">
    This advanced system uses <b>Quantum-Inspired algorithms</b> to correlate your genetic markers (SNPs) 
    with Traditional Chinese Medicine (TCM) patterns. It simulates a health wavefunction that explores 
    all potential recommendations before 'collapsing' into the most effective plan for you.
    </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🔍 Input Your Data")
        snp_list = st.multiselect(
            "Select Genetic Markers (SNPs)",
            ["MTHFR_CT", "COMT_AA", "VDR_TA", "GSTP1_GG", "MTR_AA", "NOS3_CT"],
            help="Select the SNP variants from your genetic report."
        )
        
        uploaded_file = st.file_uploader("Or upload raw DNA data (CSV/TXT)", type=['csv', 'txt'])
        if uploaded_file:
            st.success("File uploaded! YuanYingCore will parse this for relevant SNPs.")

        lab_values = st.text_area("Lab Values (e.g., B12: 400, Folate: 10)", placeholder="Enter relevant blood marker values...")
        symptoms = st.text_area("Current Symptoms", placeholder="e.g., fatigue, poor sleep, bloating...")
        health_goal = st.selectbox(
            "Primary Health Goal",
            ["Improve Energy", "Better Sleep", "Stress Reduction", "Digestive Health", "Skin Radiance"]
        )

        analyze_btn = st.button("🚀 Run YuanYingCore Analysis", use_container_width=True)

    if analyze_btn:
        if not snp_list:
            st.error("Please select at least one genetic marker.")
        else:
            with st.spinner("🌀 Initializing Quantum Wavefunction..."):
                core = YuanYingCore()
                
                # Cycle 1: Superposition
                st.info("🔄 **Cycle 1: Superposition (Hadamard Expansion)**")
                st.write("Creating all possible health states based on your Genetic-TCM entanglement...")
                status1 = core.cycle_1_superposition(snp_list, lab_values, symptoms)
                st.success(status1)
                
                # Visualization of Matrix
                st.markdown("#### 🕸️ Entanglement Matrix")
                st.dataframe(core.correlation_matrix[core.correlation_matrix['SNP_Marker'].isin(snp_list)])

                # Cycle 2: Coherent Processing
                st.info("🔄 **Cycle 2: Coherent Processing (Interference)**")
                st.write("Applying Quantum Gates (Pauli-X, CNOT) to resolve contradictions and stabilize coherence...")
                status2 = core.cycle_2_coherent_processing()
                st.success(status2)

                # Cycle 3: Collapse
                st.info("🔄 **Cycle 3: Wavefunction Collapse (Measurement)**")
                st.write(f"Collapsing all possibilities into a single reality based on your goal: {health_goal}")
                results = core.cycle_3_collapse(health_goal)
                st.success("Analysis Complete. Reality stabilized.")

                # Final Recommendations
                st.markdown("### 📜 Your Personalized Health Plan")
                
                # Fetch all recommendation details for display
                all_recs = core.generate_all_recommendations(snp_list, symptoms)
                rec_map = {r['id']: r for r in all_recs}
                
                final_plan_text = ""
                for rec_id, prob in results:
                    if rec_id in rec_map:
                        rec = rec_map[rec_id]
                        st.markdown(f"**{rec['text']}** ({rec['type']})")
                        st.write(f"Confidence Level: {prob*100:.1f}% | Focus: {', '.join(rec['tcm_focus'])}")
                        final_plan_text += f"- {rec['text']} ({rec['type']}): Focus on {', '.join(rec['tcm_focus'])}\n"

                # AI Explanation using Groq
                st.markdown("### 🤖 AI Practitioner's Insights")
                explanation_prompt = f"""
                As NutriBot V2, explain the results of the YuanYingCore analysis.
                User SNPs: {', '.join(snp_list)}
                User Goal: {health_goal}
                Recommendations: {final_plan_text}
                
                Please explain:
                1. How these genetic markers (SNPs) affect their TCM patterns.
                2. Why these specific recommendations were chosen in the quantum 'collapse'.
                3. How this helps them reach their goal of {health_goal}.
                Use simple, caring language. Explain the quantum terms (Superposition, Entanglement, Collapse) in a TCM context.
                """
                
                try:
                    explanation_response = client.chat.completions.create(
                        model=MODEL_PRIMARY,
                        messages=[
                            {"role": "system", "content": personality},
                            {"role": "user", "content": explanation_prompt}
                        ],
                        max_tokens=800
                    )
                    explanation_text = explanation_response.choices[0].message.content
                    st.markdown(explanation_text)
                except Exception as e:
                    st.error(f"Could not generate AI explanation: {e}")
                    explanation_text = "AI explanation unavailable."

                # PDF Export
                st.markdown("---")
                if st.button("📥 Export Health Plan as PDF"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(200, 10, txt="NutriBot V2 - Personalized Health Plan", ln=1, align='C')
                    pdf.set_font("Arial", size=12)
                    pdf.ln(10)
                    pdf.cell(200, 10, txt=f"Goal: {health_goal}", ln=1)
                    pdf.cell(200, 10, txt=f"SNPs: {', '.join(snp_list)}", ln=1)
                    pdf.ln(5)
                    pdf.multi_cell(0, 10, txt="Recommendations:\n" + final_plan_text)
                    pdf.ln(5)
                    pdf.set_font("Arial", 'I', 10)
                    pdf.multi_cell(0, 10, txt="AI Insights:\n" + explanation_text)
                    
                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    st.download_button(
                        label="Click here to download PDF",
                        data=pdf_output,
                        file_name="NutriBot_Health_Plan.pdf",
                        mime="application/pdf"
                    )

st.markdown('''
<div style="text-align:center;
padding:2rem;
border-top:2px solid rgba(201,168,76,0.3);
margin-top:2rem;">
<div style="color:#c9a84c;
font-family:Georgia,serif;
font-size:1.2rem;
font-weight:700;
letter-spacing:2px;
margin-bottom:0.5rem;">
NutriBot V2 — Holistic Wellness Powered by AI
</div>
<div style="color:#1a5c38;
font-size:1rem;
font-weight:600;
margin-bottom:0.3rem;">
A proprietary wellness platform by NutriBot Co. Ltd.
</div>
<div style="color:#555555;
font-size:0.85rem;
margin-bottom:0.8rem;">
© 2026 NutriBot Co. Ltd. All rights reserved.
</div>
<div style="color:#888888;
font-size:0.75rem;
font-style:italic;">
⚕️ For educational purposes only. Please consult 
a qualified healthcare professional for proper 
diagnosis and treatment.
</div>
</div>
''', unsafe_allow_html=True)
