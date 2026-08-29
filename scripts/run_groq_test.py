import os
from dotenv import load_dotenv
from groq import Groq

# Import RAG utilities
from nutribot.rag import (
    load_tcm_constitutions,
    load_tcm_herbs_formulas,
    find_relevant_constitutions,
    find_relevant_herbs_formulas,
    build_rag_context,
)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("GROQ_API_KEY not found in environment/.env — cannot run live test.")
    raise SystemExit(1)

client = Groq(api_key=GROQ_API_KEY)
MODEL = os.getenv("MODEL_PRIMARY", "openai/gpt-oss-20b")

# Load knowledge bases
consts = load_tcm_constitutions()
herbs = load_tcm_herbs_formulas()

prompts = [
    "Saya sering merasa lelah dan mudah masuk angin, apa yang harus saya lakukan?",
    "Apa manfaat jahe untuk kesehatan?",
    "Saya hamil, apakah aman minum teh kayu manis?",
]

# Personality and grounding rules copied from app.py to mirror live system prompt
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

rag_grounding_rules = (
    "RAG GROUNDING & SAFETY INSTRUCTIONS:\n"
    "- When reference data from the TCM Knowledge Base (Body Constitutions or Herbs & Formulas) is provided above, answer primarily based on that data, explicitly mention which constitution type(s) or herb/formula name(s) it relates to, and do NOT contradict the provided reference data.\n"
    "- SAFETY MANDATE: When herb or formula reference data is provided, you MUST include the Cautions & Contraindications field content in your response whenever relevant. Do not omit contraindications.\n"
    "- CRITICAL SAFETY RULE: If a user mentions taking medication, underlying health conditions, or being pregnant, and a matched herb/formula has contraindications for those conditions, explicitly highlight the warning to the user.\n"
    "- If no reference data matches the query, answer more generally using established TCM principles, but do NOT fabricate specific formula names, dosages, or unverified herb pairings."
)

language_directive = "You are a TCM assistant. Answer the user in Bahasa Indonesia only. Do not use English or any other language."

for i, prompt in enumerate(prompts, start=1):
    print(f"\n--- Prompt {i} ---\n{prompt}\n")
    matched_constitutions = find_relevant_constitutions(prompt, consts)
    matched_herbs = find_relevant_herbs_formulas(prompt, herbs, matched_constitutions=matched_constitutions)

    matched_c_names = [f"{m['name_english']} ({m['name_chinese']})" for m in matched_constitutions]
    matched_h_names = [f"{h['name_english']} ({h['name_chinese']})" for h in matched_herbs]

    print("Matched Constitutions:", matched_c_names)
    print("Matched Herbs/Formulas:", matched_h_names)

    rag_context = build_rag_context(matched_constitutions, matched_herbs)
    print("\nRAG Context:\n", rag_context)

    system_prompt = f"{personality}\n\n{rag_context}\n\n{rag_grounding_rules}\n\nSelected language: id\n{language_directive}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
            stream=False
        )
        content = completion.choices[0].message.content
        print("\nModel response:\n")
        print(content)
    except Exception as e:
        print("ERROR calling Groq:", e)

print('\nTest run complete.')
