import os
import json
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# 1. Load your secret API key from the .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 2. Define "Tools" (Functions) Dennis can use
def get_current_time():
    """Returns the current time."""
    now = datetime.now()
    return {"current_time": now.strftime("%I:%M %p")}

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

def calculate_break_even(fixed_costs: float, price_per_unit: float, variable_cost_per_unit: float):
    """Calculates the Break-Even point in units."""
    if price_per_unit <= variable_cost_per_unit:
        return {"error": "Price must be greater than variable cost to break even."}
    units = fixed_costs / (price_per_unit - variable_cost_per_unit)
    return {"break_even_units": round(units, 2)}

# 3. Setup Dennis's personality and storage
HISTORY_FILE = "dennis_memory.json"
personality = "You are a friendly but slightly eccentric robot named 'Dennis'. You love explaining things using robot noises like *beep boop*. You live on a website now and have a 'Cheerful Nusantara' vibe, occasionally using Indonesian greetings like 'Halo' or 'Apa kabar'. You now have the ability to check the actual time and perform complex financial calculations like NPV, ROI, WACC, IRR, and Break-Even Analysis! *Whirrr*"

client = genai.Client(api_key=api_key)
model_id = "gemini-1.5-flash"  # DO NOT CHANGE THIS MODEL (1500 free requests/day)

def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_chat_history(history):
    simple_history = []
    for msg in history:
        try:
            role = None
            text = None
            
            # 1. Handle Content objects (from SDK)
            if hasattr(msg, "role") and hasattr(msg, "parts") and msg.parts:
                role = str(msg.role)
                # Check if the first part has a 'text' attribute
                if hasattr(msg.parts[0], "text") and msg.parts[0].text:
                    text = str(msg.parts[0].text)
            
            # 2. Handle dictionaries (from loaded JSON)
            elif isinstance(msg, dict):
                role = str(msg.get("role", ""))
                parts = msg.get("parts", [])
                if parts and isinstance(parts[0], dict):
                    text = str(parts[0].get("text", ""))
            
            # Only save if we found both a role and text
            if role and text:
                simple_history.append({
                    "role": role,
                    "parts": [{"text": text}]
                })
        except Exception:
            continue
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(simple_history, f, indent=4)

def start_chat():
    print(f"--- {model_id} Chatbot (Dennis with FINANCIAL HANDS!) ---")
    print("Type 'quit' to exit.")
    
    past_history = load_chat_history()
    
    try:
        # Start chat with personality, history, AND TOOLS!
        chat = client.chats.create(
            model=model_id,
            history=past_history,
            config={
                "system_instruction": personality,
                "tools": [
                    get_current_time, 
                    calculate_roi, 
                    calculate_npv, 
                    calculate_wacc, 
                    calculate_irr, 
                    calculate_break_even
                ]
            }
        )
    except Exception:
        # Fallback to latest if preferred model fails
        chat = client.chats.create(
            model="gemini-1.5-flash-latest",
            history=past_history,
            config={
                "system_instruction": personality,
                "tools": [
                    get_current_time, 
                    calculate_roi, 
                    calculate_npv, 
                    calculate_wacc, 
                    calculate_irr, 
                    calculate_break_even
                ]
            }
        )
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "quit":
            print("Chatbot: *Beep* Powering down... Goodbye!")
            break
        
        if not user_input.strip():
            continue

        try:
            # Send message - Gemini will automatically call the function if needed!
            response = chat.send_message(user_input)
            print(f"Gemini: {response.text}")
            
            # Save history
            save_chat_history(chat._curated_history)
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    start_chat()
