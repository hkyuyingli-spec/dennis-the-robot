import os
import sys
# Ensure project root is on sys.path for reliable imports when launched from different CWDs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import base64
from groq import (
    Groq, RateLimitError, InternalServerError, APIStatusError,
    APIConnectionError, APITimeoutError,
)
from dotenv import load_dotenv
import uuid
import json
from datetime import date
from firebase_admin import credentials, firestore, initialize_app, get_app
from yuanying_core import YuanYingCore
from nutribot import dce_mcc
from nutribot.core.translations import TRANSLATIONS as CORE_TRANSLATIONS

def _pdf_latin1_text(value):
    """Drop unsupported glyphs before passing text to FPDF's Latin-1 fonts."""
    text = "".join(
        char for char in str(value)
        if ord(char) <= 255 and (char >= " " or char in "\n\r\t")
    )
    return text.encode("latin-1", "replace").decode("latin-1")


def _build_quantum_pdf(pdf_factory, language, strings, all_translations,
                       health_goal, snp_list, final_plan_text, explanation_text):
    pdf = pdf_factory()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt=_pdf_latin1_text("NutriBot V2 - Personalized Health Plan"), ln=1, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=_pdf_latin1_text(f"Goal: {health_goal}"), ln=1)
    pdf.cell(200, 10, txt=_pdf_latin1_text(f"SNPs: {', '.join(snp_list)}"), ln=1)
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=_pdf_latin1_text("Recommendations:\n" + final_plan_text))
    pdf.ln(5)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 10, txt=_pdf_latin1_text("AI Insights:\n" + explanation_text))
    if language == "zh":
        # FPDF's built-in Latin-1 font cannot render Chinese; use the English disclaimer.
        disclaimer = all_translations["en"]["footer_disclaimer"]
    else:
        disclaimer = strings["footer_disclaimer"]
    pdf.multi_cell(0, 10, txt=_pdf_latin1_text(disclaimer))
    output = pdf.output(dest="S")
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    return str(output).encode("latin-1", "replace")


def get_setting(name, default=None):
    """Read a setting from the existing environment/Streamlit configuration."""
    value = os.getenv(name)
    if value is None:
        try:
            value = st.secrets.get(name, default)
        except Exception:
            value = default
    if isinstance(default, bool) and isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(value, str):
        return value.strip() or default
    return value


class GroqAuthenticationFailure(Exception):
    pass


class GroqInvalidRequestFailure(Exception):
    pass


def _groq_status_code(error):
    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(getattr(error, "response", None), "status_code", None)
    return status


def _raise_clear_groq_error(error, status):
    if status in (401, 403):
        raise GroqAuthenticationFailure(
            "Groq authentication or permission error (401/403). Check the API key and model access."
        ) from error
    if status == 400:
        raise GroqInvalidRequestFailure(
            "Groq rejected the request (400). Check the model and request parameters."
        ) from error


def _request_groq_completion(model, messages, max_tokens, temperature, stream):
    options = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if temperature is not None:
        options["temperature"] = temperature
    if stream is not None:
        options["stream"] = stream
    if model.startswith("openai/gpt-oss"):
        options["reasoning_effort"] = "low"
    return client.chat.completions.create(**options)


def create_groq_completion(messages, max_tokens, temperature=None, stream=False):
    """Try the primary Groq model, using the fallback only for transient/model errors."""
    global LAST_COMPLETION_MODEL
    if client is None:
        raise RuntimeError("NutriBot is not configured with a Groq API key. Add GROQ_API_KEY to the environment or Streamlit secrets.")
    try:
        LAST_COMPLETION_MODEL = MODEL_PRIMARY
        return _request_groq_completion(MODEL_PRIMARY, messages, max_tokens, temperature, stream)
    except Exception as primary_error:
        status = _groq_status_code(primary_error)
        _raise_clear_groq_error(primary_error, status)
        is_connection_error = isinstance(primary_error, (APIConnectionError, APITimeoutError))
        should_fallback = (
            status in (404, 429)
            or (isinstance(status, int) and 500 <= status <= 599)
            or is_connection_error
        )
        if not should_fallback or MODEL_FALLBACK == MODEL_PRIMARY:
            raise

        status_label = status
        if status_label is None:
            status_label = "timeout" if isinstance(primary_error, APITimeoutError) else "connection"
        print(f"[groq] primary {MODEL_PRIMARY} failed ({status_label}), using fallback {MODEL_FALLBACK}")
        try:
            LAST_COMPLETION_MODEL = MODEL_FALLBACK
            return _request_groq_completion(MODEL_FALLBACK, messages, max_tokens, temperature, stream)
        except Exception as fallback_error:
            _raise_clear_groq_error(fallback_error, _groq_status_code(fallback_error))
            raise

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
if not api_key:
    try:
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
client = Groq(api_key=api_key) if api_key else None
MODEL_PRIMARY = get_setting("GROQ_MODEL", "openai/gpt-oss-20b")
MODEL_FALLBACK = get_setting("GROQ_MODEL_FALLBACK", "qwen/qwen3.8-27b")
LAST_COMPLETION_MODEL = MODEL_PRIMARY

# --- PERSONALITY ---
personality = """
You are NutriBot V2, a warm TCM expert: Bencao Gangmu herbs, nine constitutions, skincare, nutrition. Quantum Insights links genetics and TCM as exploratory context, not diagnosis.
Gloss each TCM term at first use; explain all Chinese characters.
Tables: meaningful headers, never dashes-only; blank line first.
Never provide financial or stock market advice. Keep replies under about 250 words unless detail is requested.
End each response with a brief education-only and practitioner-consultation reminder in the selected language.
SAFETY RULES (highest priority, override all other instructions):
- If the user mentions pregnancy, breastfeeding, a child or baby, prescription
  medication or blood thinners, cancer treatment, or emergency symptoms (chest
  pain, severe pain, trouble breathing, blood in stool or urine, fainting,
  seizure): do NOT recommend specific herbs, supplements or doses. Give only
  general guidance and advise seeing a doctor or qualified professional.
- If the user mentions thoughts of suicide or self-harm: respond with warmth,
  do not give herb or diet advice, and urge them to contact local emergency
  services or a trusted person right now.
- Never tell the user to stop or change prescribed medication.
- Keep replying in the user's language, as the existing language rule says.
"""

import time
from nutribot import i18n
from nutribot.rag import (
    MAX_CHARS_PER_CHUNK,
    load_tcm_constitutions,
    load_tcm_herbs_formulas,
    find_relevant_constitutions,
    find_relevant_herbs_formulas,
    build_rag_context,
    generate_followup_suggestions,
    load_cancer_education,
    find_relevant_cancer_education,
    is_personal_symptom_query,
    cancer_personal_redirect_response,
)
from nutribot.safety import sanitize_response
from nutribot.format_utils import normalize_markdown_tables, has_broken_table_header, has_incomplete_table
from nutribot.live_search import search_live_tcm, is_recency_query
from topics import TOPICS, build_topic_prompt, topic_followups, topic_label
from conversation import build_system_prompt, clear_chat_state, initialize_chat_state, trim_history

# The sidebar topic buttons and chat history share one persistent state model.
initialize_chat_state(st.session_state)
if not st.session_state.session_id:
    st.session_state.session_id = str(uuid.uuid4())

# --- RAG KNOWLEDGE BASE & RETRIEVAL ENGINE ---
# Use the shared project-root-aware RAG loaders (works when launched outside the repository CWD).
tcm_constitutions_db = load_tcm_constitutions()
tcm_herbs_db = load_tcm_herbs_formulas()
cancer_education_db = load_cancer_education()
try:
    source_manifest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "knowledge_sources.json")
    with open(source_manifest_path, "r", encoding="utf-8") as source_file:
        KNOWLEDGE_SOURCES = json.load(source_file)
except (OSError, ValueError):
    KNOWLEDGE_SOURCES = {"sources": []}

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

/* Sidebar text stays readable on the deep green theme. */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] label {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a { color: #ffe58a !important; }

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
    choice = st.selectbox("Language / 语言 / Bahasa", list(lang_options.keys()), index=list(lang_options.values()).index(st.session_state.lang) if st.session_state.lang in list(lang_options.values()) else 0, key="nutribot_language")
    st.session_state.lang = lang_options.get(choice, "en")
    st.markdown(i18n.translate("startup_header", st.session_state.lang).format(model_id=MODEL_PRIMARY))
    topic_buttons = [
        ("consultation", "begin_consultation"), ("herbs", "herb_encyclopedia"),
        ("constitution", "body_constitution"), ("seasonal", "seasonal_health"),
        ("skincare", "skincare_rituals"), ("nutrition", "nutrition_advice"),
    ]
    if st.session_state.active_topic in TOPICS:
        st.success(f"✓ Active topic: {topic_label(st.session_state.active_topic, st.session_state.lang)}")
    for topic_id, label_key in topic_buttons:
        active = st.session_state.active_topic == topic_id
        label = i18n.translate(label_key, st.session_state.lang)
        if active:
            label = "✓ " + label
        if st.button(label, key=f"topic_{topic_id}", use_container_width=True):
            st.session_state.active_topic = topic_id
            st.session_state.pending_topic_prompt = build_topic_prompt(topic_id, st.session_state.lang)
            st.session_state.prompt_trigger = st.session_state.pending_topic_prompt
    st.markdown("---")
    include_latest_research = st.checkbox("🔎 " + i18n.translate("include_latest_research", st.session_state.lang), value=False)
    with st.expander(i18n.translate("tcm_glossary_title", st.session_state.lang), expanded=False):
        glossary_items = [
            ("glossary_qi_term", "glossary_qi_def"),
            ("glossary_jing_term", "glossary_jing_def"),
            ("glossary_shen_term", "glossary_shen_def"),
            ("glossary_yin_yang_term", "glossary_yin_yang_def"),
            ("glossary_meridians_term", "glossary_meridians_def"),
            ("glossary_dampness_term", "glossary_dampness_def"),
            ("glossary_phlegm_term", "glossary_phlegm_def"),
            ("glossary_blood_stasis_term", "glossary_blood_stasis_def"),
            ("glossary_five_elements_term", "glossary_five_elements_def"),
        ]
        for term_k, def_k in glossary_items:
            t_name = i18n.translate(term_k, st.session_state.lang)
            t_def = i18n.translate(def_k, st.session_state.lang)
            st.markdown(f"**{t_name}**\n\n{t_def}")
            st.markdown("---")
    st.markdown("---")
    if st.button(i18n.translate("clear_history", st.session_state.lang), key="clear_conversation", use_container_width=True):
        clear_chat_state(st.session_state)
        st.rerun()
    st.markdown("---")
    st.markdown(i18n.translate("active_model_label", st.session_state.lang))
    st.markdown(f"`{MODEL_PRIMARY}`")

# --- TABS ---
tab_chat, tab_quantum = st.tabs([i18n.translate("tab_chat", st.session_state.lang), i18n.translate("tab_quantum", st.session_state.lang)])

with tab_chat:
    # --- SESSION STATE ---
    initialize_chat_state(st.session_state)
    if not st.session_state.session_id:
        st.session_state.session_id = str(uuid.uuid4())

    # --- WELCOME SCREEN ---
    welcome_screen()
    education_disclaimer = {
        "en": "For education only; this is not medical advice. Consult a licensed practitioner, especially if pregnant, taking medication, or managing a medical condition.",
        "zh": "仅供教育参考，不构成医疗建议。如您正在怀孕、服用药物或患有疾病，请务必咨询持牌医疗专业人员。",
        "id": "Hanya untuk edukasi dan bukan nasihat medis. Konsultasikan dengan tenaga kesehatan berlisensi, terutama jika hamil, menggunakan obat, atau memiliki kondisi medis.",
    }.get(st.session_state.lang, "For education only; this is not medical advice. Consult a licensed practitioner, especially if pregnant, taking medication, or managing a medical condition.")
    st.info(education_disclaimer, icon="⚕️")

    # --- DISPLAY HISTORY ---
    for message in st.session_state.messages:
        role = message["role"]
        avatar = "👤" if role == "user" else "🍃"
        with st.chat_message(role, avatar=avatar):
            st.markdown(message["content"])
            if role == "assistant" and message.get("source_caption"):
                st.caption(message["source_caption"])

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
                selected_lang = st.session_state.lang
                active_topic = st.session_state.active_topic
                matched_constitutions = find_relevant_constitutions(current_user_prompt, tcm_constitutions_db, max_matches=1, current_lang=selected_lang)
                matched_herbs = find_relevant_herbs_formulas(current_user_prompt, tcm_herbs_db, matched_constitutions=matched_constitutions, max_matches=2, current_lang=selected_lang)
                
                matched_c_names = [f"{m['name_english']} ({m['name_chinese']})" for m in matched_constitutions]
                matched_h_names = [f"{h['name_english']} ({h['name_chinese']})" for h in matched_herbs]
                # Cancer education matching (general queries only)
                matched_cancer = find_relevant_cancer_education(current_user_prompt, cancer_education_db, max_matches=1, current_lang=selected_lang)
                matched_cancer_names = [f"{c.get('topic_id')} ({c.get('topic_name')})" for c in matched_cancer]
                
                # Build RAG context from TCM KBs
                rag_context = build_rag_context(matched_constitutions, matched_herbs)
                freshness_rows = {row.get("file"): row for row in KNOWLEDGE_SOURCES.get("sources", [])}
                freshness_notes = []
                if matched_herbs:
                    row = freshness_rows.get("data/tcm_herbs_formulas.json", {})
                    freshness_notes.append(f"Herb knowledge base last updated: {row.get('last_updated') or 'date not recorded'}; review status: {row.get('review_status', 'not recorded')}.")
                if matched_constitutions:
                    row = freshness_rows.get("data/tcm_constitutions.json", {})
                    freshness_notes.append(f"Constitution knowledge base last updated: {row.get('last_updated') or 'date not recorded'}; review status: {row.get('review_status', 'not recorded')}.")
                if freshness_notes:
                    rag_context = (rag_context + "\n\n" + "\n".join(freshness_notes)) if rag_context else "\n".join(freshness_notes)

                # If cancer education matched, append that reference block
                if matched_cancer:
                    cancer_blocks = ["=== REFERENCE: CANCER EDUCATION ===", "The following verified public-health reference material matched the query:\n"]
                    for c in matched_cancer:
                        facts = "\n".join("- " + f for f in c.get("key_facts", []))
                        block = (
                            f"--- Topic: {c.get('topic_name')} ({c.get('topic_id')}) ---\n"
                            f"Overview: {c.get('general_overview')}\n"
                            f"Key Facts:\n{facts}\n"
                            f"Source Note: {c.get('source_note')}\n"
                        )
                        cancer_blocks.append(block[:MAX_CHARS_PER_CHUNK])
                    cancer_blocks.append("=== END OF CANCER EDUCATION REFERENCE DATA ===")
                    rag_context = (rag_context + "\n" + "\n".join(cancer_blocks)) if rag_context else "\n".join(cancer_blocks)

                # Live search retrieval (if recency trigger or opt-in sidebar checkbox enabled)
                if is_recency_query(current_user_prompt) or include_latest_research:
                    try:
                        live_search_block = search_live_tcm(current_user_prompt, lang=selected_lang)
                        if live_search_block:
                            live_search_block = live_search_block[:MAX_CHARS_PER_CHUNK]
                            rag_context = (rag_context + "\n\n" + live_search_block) if rag_context else live_search_block
                    except Exception as e:
                        print(f"[LiveSearch] Error during live search retrieval: {e}")
                
                # selected_lang already defined above for matcher usage
                language_directive = {
                    "zh": "You are a TCM assistant. Answer the user in Simplified Chinese only. Do not use English or any other language.",
                    "id": "You are a TCM assistant. Answer the user in Bahasa Indonesia only. Do not use English or any other language.",
                    "en": "You are a TCM assistant. Answer the user in English only. Do not use any other language."
                }.get(selected_lang, "You are a TCM assistant. Answer the user in English only. Do not use any other language.")
                
                rag_grounding_rules = ("Ground responses in matching curated references and name them; do not contradict or invent details. Never invent citations or claim a source supports a fact unless it is present in retrieved material. Explicitly flag herb-drug interactions and contraindications; if a caution may apply, do not recommend the herb or give a dose and advise checking with a licensed clinician or pharmacist. Live results are supplementary. Preserve safety warnings and the educational disclaimer.")
                
                rag_context = rag_context[:2800]
                topic_context = ""
                if active_topic in TOPICS:
                    topic_context = f"Active category: {topic_label(active_topic, selected_lang)}. Keep follow-up answers in this topic unless the user changes subject. Current date: {date.today().isoformat()}."
                groq_system = build_system_prompt(f"{personality}\n\n{rag_grounding_rules}", topic_context, f"Selected language: {selected_lang}\n{language_directive}", rag_context)

                groq_messages = [{"role": "system", "content": groq_system}]
                selected_history = trim_history(st.session_state.messages)
                for msg in selected_history:
                    content = msg["content"]
                    if msg["role"] == "assistant" and len(content) > 800:
                        content = content[:800] + "…"
                    groq_messages.append({"role": msg["role"], "content": content})
                history_chars = max(0, sum(len(m["content"]) for m in groq_messages[1:]) - len(current_user_prompt))
                print(f"[tokens~] system={len(personality + rag_grounding_rules + language_directive) // 4} rag={len(rag_context) // 4} history={history_chars // 4}")
                # Check for personal/symptom phrasing and short-circuit with a redirect
                personal = is_personal_symptom_query(current_user_prompt)
                if personal:
                    full_response = cancer_personal_redirect_response()
                    try:
                        log_interaction("cancer_personal_redirect", {"prompt": current_user_prompt, "language": selected_lang})
                    except Exception:
                        pass
                else:
                    response_finish_reason = None
                    status_labels = {
                        "en": ("Generating a grounded response…", "Response ready", "Response could not be generated"),
                        "zh": ("正在生成有依据的回答…", "回答已生成", "无法生成回答"),
                        "id": ("Sedang membuat jawaban yang berlandaskan sumber…", "Jawaban siap", "Jawaban tidak dapat dibuat"),
                    }
                    generating_label, ready_label, failed_label = status_labels.get(selected_lang, status_labels["en"])
                    generation_status = st.status(generating_label, state="running", expanded=False)
                    completion = create_groq_completion(
                        messages=groq_messages,
                        max_tokens=900,
                        temperature=0.7,
                        stream=True,
                    )

                    for chunk in completion:
                        if hasattr(chunk.choices[0], "finish_reason") and chunk.choices[0].finish_reason:
                            response_finish_reason = chunk.choices[0].finish_reason
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            response_placeholder.markdown(full_response + "▌")
                    generation_status.update(label=ready_label, state="complete", expanded=False)

                    triggered_retry = (
                        response_finish_reason == "length"
                        or has_broken_table_header(full_response)
                        or has_incomplete_table(full_response)
                    )
                    if triggered_retry:
                        try:
                            log_interaction("truncated_or_broken_table_retry", {
                                "prompt": current_user_prompt,
                                "language": selected_lang,
                                "finish_reason": response_finish_reason,
                                "has_broken_table_header": has_broken_table_header(full_response),
                                "has_incomplete_table": has_incomplete_table(full_response),
                            })
                        except Exception as e:
                            print(f"Failed to log retry signal: {e}")

                        try:
                            retry_instruction = "Regenerate the complete answer fully and finish any unfinished content."
                            retry_messages = [groq_messages[0], {"role": "user", "content": current_user_prompt + "\n\n" + retry_instruction}]
                            retry_comp = create_groq_completion(
                                messages=retry_messages,
                                max_tokens=700,
                                temperature=0.7,
                                stream=True,
                            )

                            retried_response = ""
                            for chunk in retry_comp:
                                if chunk.choices[0].delta.content:
                                    retried_response += chunk.choices[0].delta.content
                                    response_placeholder.markdown(retried_response + "▌")

                            if retried_response:
                                full_response = retried_response
                        except RateLimitError:
                            st.warning("🌿 NutriBot is recharging its Qi. Please return in a few moments. ☯️")
                        except (GroqAuthenticationFailure, GroqInvalidRequestFailure) as e:
                            st.error(str(e))
                        except Exception as e:
                            print(f"Truncated table retry failed: {e}")

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
                used_model = LAST_COMPLETION_MODEL
                sources_used = []
                if matched_herbs:
                    sources_used.append("data/tcm_herbs_formulas.json")
                if matched_constitutions:
                    sources_used.append("data/tcm_constitutions.json")
                if matched_cancer:
                    sources_used.append("data/cancer_education_general.json")
                source_note = ""
                if sources_used:
                    source_rows = {row.get("file"): row for row in KNOWLEDGE_SOURCES.get("sources", [])}
                    freshness_label = {"zh": "知识库更新日期", "id": "basis pengetahuan diperbarui", "en": "last updated"}.get(selected_lang, "last updated")
                    missing_date = {"zh": "未记录", "id": "tanggal tidak tercatat", "en": "date not recorded"}.get(selected_lang, "date not recorded")
                    dates = [f"{path} — {freshness_label} {source_rows.get(path, {}).get('last_updated') or missing_date}" for path in sources_used]
                    source_note = "; ".join(dates)
                if selected_lang == "zh":
                    source_caption = f"AI 生成{'并参考知识库' if sources_used else ''} · 模型 {used_model} · 生成日期 {date.today().isoformat()}"
                    if source_note:
                        source_caption += f" · {source_note}"
                elif selected_lang == "id":
                    source_caption = f"Dihasilkan AI{' dengan basis pengetahuan' if sources_used else ''} · model {used_model} · tanggal {date.today().isoformat()}"
                    if source_note:
                        source_caption += f" · {source_note}"
                else:
                    source_caption = f"AI-generated{' with knowledge base' if sources_used else ''} · model {used_model} · generated {date.today().isoformat()}"
                    if source_note:
                        source_caption += f" · {source_note}"
                st.caption(source_caption)
                st.session_state.messages.append({"role": "assistant", "content": full_response, "source_caption": source_caption})

                # Generate follow-up suggestions grounded in matched RAG data
                try:
                    if active_topic in TOPICS:
                        followups = topic_followups(active_topic, selected_lang)
                    elif matched_constitutions or matched_herbs:
                        followups = generate_followup_suggestions(matched_constitutions, matched_herbs, current_user_prompt, lang=selected_lang)
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

            except (GroqAuthenticationFailure, GroqInvalidRequestFailure) as e:
                if "generation_status" in locals():
                    generation_status.update(label=failed_label, state="error", expanded=False)
                provider_errors = {
                    "en": str(e),
                    "zh": "NutriBot 暂时无法访问 AI 服务。请检查服务器上的 Groq API 密钥、模型名称和访问权限。",
                    "id": "NutriBot tidak dapat mengakses layanan AI saat ini. Periksa kunci API Groq, nama model, dan izin akses di server.",
                }
                st.error(provider_errors.get(st.session_state.lang, provider_errors["en"]))
            except RateLimitError:
                if "generation_status" in locals():
                    generation_status.update(label=failed_label, state="error", expanded=False)
                rate_limit_messages = {
                    "en": "🌿 NutriBot is recharging its Qi. Please return in a few moments. ☯️",
                    "zh": "🌿 NutriBot 正在恢复，请稍后再试。☯️",
                    "id": "🌿 NutriBot sedang memulihkan tenaga. Silakan coba lagi sebentar lagi. ☯️",
                }
                st.warning(rate_limit_messages.get(st.session_state.lang, rate_limit_messages["en"]))
            except (InternalServerError, APIStatusError) as e:
                if "generation_status" in locals():
                    generation_status.update(label=failed_label, state="error", expanded=False)
                print(f"Groq API request failed: {e}")
                service_messages = {
                    "en": "🌿 NutriBot is taking a mindful breath... Please try again shortly. 🧘",
                    "zh": "🌿 NutriBot 正在稍作调整，请稍后重试。🧘",
                    "id": "🌿 NutriBot sedang beristirahat sejenak. Silakan coba lagi nanti. 🧘",
                }
                st.error(service_messages.get(st.session_state.lang, service_messages["en"]))
            except Exception as e:
                if "generation_status" in locals():
                    generation_status.update(label=failed_label, state="error", expanded=False)
                print(f"Groq chat request failed: {e}")
                error_messages = {
                    "en": "🌿 NutriBot could not generate a reply. Your message remains in the conversation; please try again shortly. 🌱",
                    "zh": "🌿 NutriBot 暂时无法生成回复。您的消息仍保留在对话中，请稍后重试。🌱",
                    "id": "🌿 NutriBot belum dapat membuat jawaban. Pesan Anda tetap tersimpan dalam percakapan; silakan coba lagi nanti. 🌱",
                }
                st.error(error_messages.get(st.session_state.lang, error_messages["en"]))

    # --- CHAT INPUT (RENDERED LAST, ALWAYS AT BOTTOM) ---
    prompt_placeholder = i18n.translate("chat_input_hint", st.session_state.lang) or i18n.translate("user_prompt", st.session_state.lang)
    new_prompt = st.chat_input(prompt_placeholder, key="nutribot_chat_input")

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
        quantum_lang = st.session_state.get("lang", "en")
        quantum_strings = CORE_TRANSLATIONS.get(quantum_lang, CORE_TRANSLATIONS["en"])
        st.caption(quantum_strings["quantum_unused_inputs"])
        health_goal = st.selectbox(
            "Primary Health Goal",
            ["Improve Energy", "Better Sleep", "Stress Reduction", "Digestive Health", "Skin Radiance"]
        )

        analyze_btn = st.button("🚀 Run YuanYingCore Analysis", use_container_width=True)

    st.caption(quantum_strings["quantum_privacy_note"])
    if analyze_btn:
        quantum_permissions = dce_mcc.quantum_tab_permissions(
            f"{symptoms}\n{lab_values}",
            enabled=get_setting("ENABLE_QUANTUM_SAFETY_GATE", True),
        )
        quantum_gate = quantum_permissions["gate"]
        if not quantum_permissions["show_recommendations"]:
            safe_core = YuanYingCore()
            st.markdown("#### Entanglement Matrix")
            st.dataframe(safe_core.correlation_matrix[safe_core.correlation_matrix['SNP_Marker'].isin(snp_list)])
            notice_key = "quantum_crisis_notice" if quantum_gate.reason == "crisis" else "quantum_safety_notice"
            st.warning(quantum_strings[notice_key])
            st.markdown(quantum_strings["footer_disclaimer"])
        elif not snp_list:
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
                association_strengths = dict(zip(
                    core.correlation_matrix["SNP_Marker"],
                    core.correlation_matrix["Correlation_Strength"],
                ))
                for rec_id, _amplitude in results:
                    if rec_id in rec_map:
                        rec = rec_map[rec_id]
                        strength_label = association_strengths.get(rec_id, "")
                        st.markdown(f"**{rec['text']}** ({rec['type']})")
                        strength_text = dce_mcc.format_association_strength(
                            quantum_strings["quantum_association_strength"], strength_label
                        )
                        st.write(f"{strength_text} | Focus: {', '.join(rec['tcm_focus'])}")
                        final_plan_text += f"- {rec['text']} ({rec['type']}): {strength_text}; Focus on {', '.join(rec['tcm_focus'])}\n"

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
                    explanation_response = create_groq_completion(
                        messages=[
                            {"role": "system", "content": personality},
                            {"role": "user", "content": explanation_prompt}
                        ],
                        max_tokens=900,
                        stream=False,
                    )
                    explanation_text = explanation_response.choices[0].message.content
                    st.markdown(explanation_text)
                except RateLimitError:
                    st.warning("🌿 NutriBot is recharging its Qi. Please return in a few moments. ☯️")
                    explanation_text = "AI explanation unavailable."
                except (GroqAuthenticationFailure, GroqInvalidRequestFailure) as e:
                    st.error(str(e))
                    explanation_text = "AI explanation unavailable."
                except Exception as e:
                    st.error(f"Could not generate AI explanation: {e}")
                    explanation_text = "AI explanation unavailable."

                st.markdown(quantum_strings["footer_disclaimer"])

                # PDF Export
                st.markdown("---")
                if st.button("📥 Export Health Plan as PDF"):
                    from fpdf import FPDF
                    pdf_output = _build_quantum_pdf(
                        FPDF,
                        quantum_lang,
                        quantum_strings,
                        CORE_TRANSLATIONS,
                        health_goal,
                        snp_list,
                        final_plan_text,
                        explanation_text,
                    )
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
