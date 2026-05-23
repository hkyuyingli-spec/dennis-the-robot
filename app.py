import os
import json
import streamlit as st
import yfinance as yf
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# 1. Setup & Configuration
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
HISTORY_FILE = "dennis_memory.json"
personality = "You are a friendly but slightly eccentric robot named 'Dennis'. You love explaining things using robot noises like *beep boop*. You live on a website now and have a 'Cheerful Nusantara' vibe, occasionally using Indonesian greetings like 'Halo' or 'Apa kabar'. You now have the ability to check stock prices, exchange rates, and perform complex financial calculations like NPV, ROI, WACC, and IRR! *Whirrr*"

client = genai.Client(api_key=api_key)
model_id = "gemini-2.5-flash"

# 2. Tool Definition
def get_current_time():
    """Returns the current time."""
    now = datetime.now()
    return {"current_time": now.strftime("%I:%M %p")}

def get_stock_price(symbol: str):
    """
    Get the latest price for a stock symbol or currency pair (e.g., 'AAPL', 'BTC-USD', 'USDIDR=X').
    Useful when the user asks for stock prices, exchange rates, or financial updates.
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty:
            return {"error": f"Could not find data for {symbol}. Make sure the symbol is correct."}
        
        latest_price = data['Close'].iloc[-1]
        currency = ticker.info.get('currency', 'USD')
        name = ticker.info.get('longName', symbol)
        
        return {
            "symbol": symbol,
            "name": name,
            "current_price": round(float(latest_price), 2),
            "currency": currency
        }
    except Exception as e:
        return {"error": str(e)}

def calculate_npv(cash_flows: list[float], discount_rate: float):
    """
    Calculate the Net Present Value (NPV).
    :param cash_flows: A list of cash flows (e.g., [-1000, 200, 300, 400, 500]).
    :param discount_rate: The discount rate as a decimal (e.g., 0.1 for 10%).
    """
    try:
        npv_val = sum(cf / (1 + discount_rate)**i for i, cf in enumerate(cash_flows))
        return {"npv": round(npv_val, 2)}
    except Exception as e:
        return {"error": str(e)}

def calculate_roi(investment: float, total_return: float):
    """
    Calculate the Return on Investment (ROI).
    :param investment: The initial investment amount.
    :param total_return: The total return amount.
    """
    try:
        roi_val = (total_return - investment) / investment
        return {"roi_percentage": round(roi_val * 100, 2)}
    except Exception as e:
        return {"error": str(e)}

def calculate_wacc(equity: float, debt: float, cost_of_equity: float, cost_of_debt: float, tax_rate: float):
    """
    Calculate the Weighted Average Cost of Capital (WACC).
    :param equity: Total market value of equity.
    :param debt: Total market value of debt.
    :param cost_of_equity: Cost of equity as a decimal (e.g., 0.12 for 12%).
    :param cost_of_debt: Cost of debt as a decimal (e.g., 0.05 for 5%).
    :param tax_rate: Corporate tax rate as a decimal (e.g., 0.25 for 25%).
    """
    try:
        v = equity + debt
        wacc_val = (equity / v * cost_of_equity) + (debt / v * cost_of_debt * (1 - tax_rate))
        return {"wacc_percentage": round(wacc_val * 100, 2)}
    except Exception as e:
        return {"error": str(e)}

def calculate_irr(cash_flows: list[float]):
    """
    Calculate the Internal Rate of Return (IRR).
    :param cash_flows: A list of cash flows (e.g., [-1000, 200, 300, 400, 500]).
    """
    try:
        def npv(rate, cf_list):
            return sum(cf / (1 + rate)**i for i, cf in enumerate(cf_list))

        def npv_derivative(rate, cf_list):
            return sum(-i * cf / (1 + rate)**(i + 1) for i, cf in enumerate(cf_list))

        rate = 0.1  # Initial guess
        for _ in range(100):
            f_val = npv(rate, cash_flows)
            f_prime = npv_derivative(rate, cash_flows)
            if abs(f_prime) < 1e-10:
                break
            new_rate = rate - f_val / f_prime
            if abs(new_rate - rate) < 1e-6:
                return {"irr_percentage": round(new_rate * 100, 2)}
            rate = new_rate
        return {"error": "Could not converge to an IRR."}
    except Exception as e:
        return {"error": str(e)}

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
            "tools": [get_current_time, get_stock_price, calculate_npv, calculate_roi, calculate_wacc, calculate_irr]
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
