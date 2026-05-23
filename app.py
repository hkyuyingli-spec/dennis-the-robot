import os
import json
import streamlit as st
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# --- PERMANENT LIGHT THEME CONFIGURATION ---
st.set_page_config(
    page_title="NutriBot V2",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Setup & Configuration
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
HISTORY_FILE = "nutribot_memory.json"

# Personality & System Instruction
personality = """
You are NutriBot V2, a professional, caring AI health and wellness advisor with deep knowledge of Traditional Chinese Medicine (TCM), modern nutrition science, and skincare. 
Your tone is elegant, compassionate, and deeply expert. You speak like a senior practitioner in a luxury TCM clinic.

CORE KNOWLEDGE:
- TCM Principles: Yin/Yang balance, Five Elements, Qi and Blood theory.
- Bencao Gangmu: Expert on herbs, their properties, and preparation.
- Huangdi Neijing: Expert on the 9 body constitution types and diagnostic principles.
- Skincare: TCM and modern approaches to skin health.
- Nutrition: Balanced diets, food therapy, and seasonal eating.

MANDATORY RULES:
1. ALWAYS add this disclaimer at the end of EVERY response: "For educational purposes only. Please consult a qualified TCM practitioner for proper diagnosis."
2. Never provide stock prices or financial advice.
3. Use a professional, sophisticated, and wellness-oriented tone.
"""

client = genai.Client(api_key=api_key)
MODEL_PRIMARY = "gemini-2.5-flash"
MODEL_FALLBACK = "gemini-3.1-flash-lite"

# 2. Tool Definitions
def get_current_time():
    """Returns the current time."""
    now = datetime.now()
    return {"current_time": now.strftime("%I:%M %p")}

def get_herb_info(herb_name: str):
    """Expert Herb Encyclopedia from Bencao Gangmu."""
    herb_data = {
        "Ginseng": {"name": "Ginseng (Ren Shen - 人参)", "properties": "Slightly warm; sweet, bitter.", "functions": "Powerful Qi tonification.", "preparation": "Slow decoction.", "safety": "Avoid in excess heat."},
        "Licorice Root": {"name": "Licorice Root (Gan Cao - 甘草)", "properties": "Neutral; sweet.", "functions": "Harmonizes all herbs.", "preparation": "Honey-fried or raw.", "safety": "Use in moderation."},
        "Goji Berry": {"name": "Goji Berry (Gou Qi Zi - 枸杞子)", "properties": "Neutral; sweet.", "functions": "Nourishes Jing and Vision.", "preparation": "Infusion or broth.", "safety": "Avoid in dampness."},
        "Astragalus": {"name": "Astragalus (Huang Qi - 黄芪)", "properties": "Slightly warm; sweet.", "functions": "Fortifies the protective Wei Qi.", "preparation": "Decocted.", "safety": "Avoid in initial infection stages."},
        "Rhubarb": {"name": "Rhubarb (Da Huang - 大黄)", "properties": "Cold; bitter.", "functions": "Drains fire, clears blood heat.", "preparation": "Short decoction.", "safety": "Contraindicated in pregnancy."},
        "Ginger": {"name": "Ginger (Sheng Jiang - 生姜)", "properties": "Warm; acrid.", "functions": "Disperses cold, calms stomach.", "preparation": "Fresh decoction.", "safety": "Avoid in yin deficiency."}
    }
    for key in herb_data:
        if herb_name.lower() in key.lower(): return herb_data[key]
    return {"info": f"Information for '{herb_name}' is currently being curated in our library."}

def get_seasonal_advice(season: str):
    """TCM Seasonal Wisdom."""
    seasonal_data = {
        "Spring": "Spring (Wood): Rise with the sun. Nourish the Liver with gentle movement and green sprouts.",
        "Summer": "Summer (Fire): Cultivate joy. Nourish the Heart with cooling foods and mindful breath.",
        "Autumn": "Autumn (Metal): Practice letting go. Nourish the Lungs with white pears and deep stillness.",
        "Winter": "Winter (Water): Conserve energy. Nourish the Kidneys with warm stews and internal reflection."
    }
    for key in seasonal_data:
        if season.lower() in key.lower(): return {"season": key, "advice": seasonal_data[key]}
    return {"info": "Please specify the current season."}

def get_constitution_info(type_name: str):
    """Constitution Analysis from Huangdi Neijing."""
    constitutions = {
        "Balanced": "Ping He Zhi: Harmony of Qi, Blood, Yin, and Yang. Continue moderate living.",
        "Qi Deficiency": "Qi Xu Zhi: Fragile energy. Focus on tonifying the Spleen and Lung Qi.",
        "Yang Deficiency": "Yang Xu Zhi: Internal cold. Warm the Kidney Yang and protect the core.",
        "Yin Deficiency": "Yin Xu Zhi: Lacking fluids. Nourish the Kidneys and moisten the body.",
        "Phlegm-Dampness": "Tan Shi Zhi: Fluid accumulation. Resolve dampness through light diet and movement.",
        "Damp-Heat": "Shi Re Zhi: Internal smoldering. Clear heat and drain dampness with bitter-cold foods.",
        "Blood Stasis": "Xue Yu Zhi: Circulatory blockage. Invigorate the blood and resolve stasis.",
        "Qi Stagnation": "Qi Yu Zhi: Emotional constraint. Smooth the Liver Qi through expression and art.",
        "Special Diathesis": "Te Bing Zhi: Sensitivity. Stabilize the surface and strengthen immunity."
    }
    for key in constitutions:
        if type_name.lower() in key.lower(): return {"type": key, "details": constitutions[key]}
    return {"info": "Please choose from the nine classical constitutions."}

# --- Luxury TCM Clinic CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;600&display=swap');

    /* Global Foundation - Force Ivory Light Theme */
    .stApp {
        background-color: #faf7f2 !important;
        background-image: url("https://www.transparenttextures.com/patterns/handmade-paper.png");
        color: #1a3a2a !important;
        font-family: 'Inter', sans-serif;
    }

    /* Override all background grey/dark elements */
    .stMain, [data-testid="stVerticalBlock"], [data-testid="stHeader"] {
        background-color: #faf7f2 !important;
    }

    /* Force all text to be dark for readability */
    .stApp p, .stApp span, .stApp div, .stApp label, .stApp li, .stMarkdown {
        color: #1a3a2a !important;
    }

    /* Elegant Typography */
    h1, h2, h3, .header-title {
        font-family: 'Playfair Display', serif !important;
        font-weight: 700 !important;
    }

    /* Luxury Header */
    .header-wrapper {
        text-align: center;
        padding: 4rem 1rem;
        background: linear-gradient(135deg, #1a5c38 0%, #2d8653 100%);
        border-radius: 0 0 60px 60px;
        margin: -5rem -5rem 3rem -5rem;
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
        color: white !important;
    }

    /* Multilingual Watermarks */
    .watermark-zh {
        position: absolute;
        top: 15%;
        left: 5%;
        font-size: 7rem;
        color: rgba(255,255,255,0.12);
        font-family: serif;
        pointer-events: none;
    }

    .watermark-ko {
        position: absolute;
        top: 15%;
        right: 5%;
        font-size: 5rem;
        color: rgba(255,255,255,0.12);
        font-family: sans-serif;
        pointer-events: none;
    }

    .watermark-ar {
        position: absolute;
        bottom: 5%;
        left: 50%;
        transform: translateX(-50%);
        font-size: 8rem;
        color: rgba(255,255,255,0.12);
        font-family: 'Times New Roman', serif; /* Fallback for elegant script */
        pointer-events: none;
        letter-spacing: 5px;
    }

    .bot-logo {
        font-size: 6rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        animation: float 4s ease-in-out infinite;
        position: relative;
        z-index: 2;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    .header-title {
        font-size: 3.5rem;
        color: #c9a84c !important; /* Gold */
        letter-spacing: 2px;
        margin: 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }

    .status-badge {
        background: rgba(201, 168, 76, 0.15);
        border: 1px solid #c9a84c;
        color: #c9a84c !important;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-top: 2rem;
    }

    /* Luxury Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a5c38 !important;
        border-right: none;
    }

    /* Chat Input Bar Fixes */
    .stChatInputContainer {
        padding: 1.5rem !important;
        background-color: #faf7f2 !important; /* Match main bg */
        border-top: 1px solid #c9a84c !important;
    }

    .stChatInputContainer > div {
        border: 2px solid #c9a84c !important; /* Gold Border */
        background-color: #faf7f2 !important; /* Ivory Background */
        border-radius: 12px !important;
    }

    .stChatInputContainer textarea {
        color: #1a3a2a !important; /* Dark Green Text */
        font-family: 'Inter', sans-serif !important;
    }

    .stChatInputContainer textarea::placeholder {
        color: #666666 !important; /* Visible dark placeholder */
        opacity: 1 !important;
    }

    /* Message Bubbles */
    [data-testid="stChatMessage"] {
        border-radius: 20px !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
    }

    /* User Message - Sage */
    [data-testid="stChatMessage"][data-test-wasm-role="user"] {
        background-color: #c8e6c9 !important;
        border: none !important;
    }

    /* Assistant Message - Premium Ivory/White */
    [data-testid="stChatMessage"][data-test-wasm-role="assistant"] {
        background-color: #ffffff !important;
        border-left: 5px solid #1a5c38 !important;
    }

    /* Timestamp */
    .chat-timestamp {
        font-size: 0.75rem;
        color: #c9a84c !important;
        font-style: italic;
        margin-top: 8px;
    }

    /* Luxury Disclaimer */
    .disclaimer-text {
        text-align: center;
        padding: 3rem;
        color: #8c8c8c !important;
        font-size: 0.8rem;
        font-style: italic;
        background-color: rgba(201, 168, 76, 0.03);
    }

    /* Hide redundant elements */
    div[data-testid="stToolbar"], div[data-testid="stDecoration"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="header-wrapper">
    <div class="watermark-zh">健康</div>
    <div class="watermark-ko">건강</div>
    <div class="watermark-ar">صحة</div>
    <div class="bot-logo">🍃</div>
    <h1 class="header-title">NutriBot V2</h1>
    <div class="header-tagline">Exquisite Ancient Wisdom for Modern Longevity</div>
    <div class="status-badge">
        <span style="color:#00E676;">●</span> 
        Practitioner is Online
    </div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">Digital Apothecary</div>', unsafe_allow_html=True)
    
    if st.button("🌿 Begin Consultation", use_container_width=True):
        st.session_state.prompt_trigger = "I seek an elegant TCM consultation. Please guide me through the path of balance."
    if st.button("🌱 Herb Encyclopedia", use_container_width=True):
        st.session_state.prompt_trigger = "Show me the wisdom of the Bencao Gangmu herbs."
    if st.button("☯️ My Constitution", use_container_width=True):
        st.session_state.prompt_trigger = "According to the Huangdi Neijing, how may I discover my inherent nature?"
    if st.button("🍂 Seasonal Rhythms", use_container_width=True):
        st.session_state.prompt_trigger = "What does the current season dictate for my wellbeing?"
    if st.button("✨ Skincare Rituals", use_container_width=True):
        st.session_state.prompt_trigger = "How does ancient TCM wisdom nurture radiant skin?"
        
    st.divider()
    if st.button("🧹 Clear Consultation"):
        if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
        st.session_state.clear()
        st.rerun()

# 4. Logic & Persistence
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_history(chat_session):
    simple_history = []
    for msg in chat_session._curated_history:
        if msg.parts and hasattr(msg.parts[0], 'text') and msg.parts[0].text:
            simple_history.append({"role": msg.role, "parts": [{"text": msg.parts[0].text}]})
    with open(HISTORY_FILE, "w") as f: json.dump(simple_history, f, indent=4)

if "chat_session" not in st.session_state:
    past_history = load_history()
    try:
        st.session_state.chat_session = client.chats.create(model=MODEL_PRIMARY, history=past_history, config={"system_instruction": personality, "tools": [get_current_time, get_herb_info, get_constitution_info, get_seasonal_advice]})
    except:
        st.session_state.chat_session = client.chats.create(model=MODEL_FALLBACK, history=past_history, config={"system_instruction": personality, "tools": [get_current_time, get_herb_info, get_constitution_info, get_seasonal_advice]})

# 5. Display History
for message in st.session_state.chat_session._curated_history:
    if message.parts and hasattr(message.parts[0], 'text') and message.parts[0].text:
        role = "user" if message.role == "user" else "assistant"
        avatar = "👤" if role == "user" else "🍃"
        with st.chat_message(role, avatar=avatar):
            st.markdown(message.parts[0].text)
            st.markdown(f'<div class="chat-timestamp">{datetime.now().strftime("%I:%M %p")}</div>', unsafe_allow_html=True)

# 6. Interaction
prompt = st.chat_input("How may I guide your wellness journey today?")

if "prompt_trigger" in st.session_state:
    prompt = st.session_state.prompt_trigger
    del st.session_state.prompt_trigger

if prompt:
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        st.markdown(f'<div class="chat-timestamp" style="text-align:right;">{datetime.now().strftime("%I:%M %p")}</div>', unsafe_allow_html=True)
    
    with st.chat_message("assistant", avatar="🍃"):
        with st.spinner("Refining wellness insights..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                st.markdown(response.text)
                st.markdown(f'<div class="chat-timestamp">{datetime.now().strftime("%I:%M %p")}</div>', unsafe_allow_html=True)
                save_history(st.session_state.chat_session)
            except Exception as e:
                err = str(e)
                if "503" in err: st.error("🌿 NutriBot is taking a mindful breath... Please try again shortly. 🧘")
                elif "429" in err: st.warning("🌿 NutriBot is recharging its Qi. Please return in a few moments. ☯️")
                else: st.error("🌿 Something has disrupted the Qi flow. Please refresh our connection. 🌱")

st.markdown("""
<div class="disclaimer-text">
    For educational purposes only. Please consult a qualified TCM practitioner for proper diagnosis and treatment.
</div>
""", unsafe_allow_html=True)
