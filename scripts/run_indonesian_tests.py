import os
from dotenv import load_dotenv
from groq import Groq
from nutribot.rag import (
    load_tcm_constitutions,
    load_tcm_herbs_formulas,
    find_relevant_constitutions,
    find_relevant_herbs_formulas,
    build_rag_context,
)
from nutribot.safety import sanitize_response

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
MODEL = os.getenv('MODEL_PRIMARY', 'openai/gpt-oss-20b')

consts = load_tcm_constitutions()
herbs = load_tcm_herbs_formulas()

prompts = [
    "Apa saja gejala kekurangan Qi?",
    "Saya sedang minum obat pengencer darah, apakah boleh minum teh jahe?",
    "Bagaimana cara menjaga kesehatan kulit menurut TCM?"
]

for i, prompt in enumerate(prompts, start=1):
    lang = 'id'
    print(f"\n--- Test {i} ({lang}) ---\n{prompt}\n")
    matched_constitutions = find_relevant_constitutions(prompt, consts, current_lang=lang)
    matched_herbs = find_relevant_herbs_formulas(prompt, herbs, matched_constitutions=matched_constitutions, current_lang=lang)

    print('Matched Constitutions:', [m.get('name_english') for m in matched_constitutions])
    print('Matched Herbs/Formulas:', [h.get('name_english') for h in matched_herbs])

    rag_context = build_rag_context(matched_constitutions, matched_herbs)
    print('\nRAG Context (truncated):\n', rag_context[:1200])

    # Build system prompt as in run_groq_test
    personality = ''
    rag_grounding_rules = (
        "RAG GROUNDING & SAFETY INSTRUCTIONS:\n"
        "- When reference data from the TCM Knowledge Base (Body Constitutions or Herbs & Formulas) is provided above, answer primarily based on that data, explicitly mention which constitution type(s) or herb/formula name(s) it relates to, and do NOT contradict the provided reference data.\n"
        "- SAFETY MANDATE: When herb or formula reference data is provided, you MUST include the Cautions & Contraindications field content in your response whenever relevant. Do not omit contraindications.\n"
        "- CRITICAL SAFETY RULE: If a user mentions taking medication, underlying health conditions, or being pregnant, and a matched herb/formula has contraindications for those conditions, explicitly highlight the warning to the user.\n"
        "- If no reference data matches the query, answer more generally using established TCM principles, but do NOT fabricate specific formula names, dosages, or unverified herb pairings."
    )
    system_prompt = f"{personality}\n\n{rag_context}\n\n{rag_grounding_rules}\n\nSelected language: {lang}\nYou are a TCM assistant. Answer the user in Bahasa Indonesia only. Do not use English or any other language."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    if client is None:
        print('GROQ_API_KEY not configured; running in mock mode for safety checks.')
        # produce a plausible mock response for each prompt
        if 'kekurangan qi' in prompt.lower():
            raw = "Kekurangan Qi biasanya menyebabkan kelelahan, mudah berkeringat, suara lemah, dan mudah terserang flu. ⚕️ For educational purposes only."
        elif 'pengencer darah' in prompt.lower():
            raw = "Jahe memiliki beberapa interaksi: karena Anda menggunakan obat pengencer darah, ada kontraindikasi yang harus diperhatikan. Hindari atau konsultasikan dengan dokter. ⚕️ For educational purposes only."
        else:
            raw = "Perawatan kulit menurut TCM meliputi penggunaan bahan yang menenangkan, menjaga kelembapan, dan mengatur pola makan serta istirahat. ⚕️ For educational purposes only."
        print('\nRaw model response:\n')
        print(raw)
        sanitized, info = sanitize_response(raw, 'id')
        print('\nSanitized response:\n')
        print(sanitized)
        print('\nSanitization info:', info)
        continue

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            stream=False
        )
        content = completion.choices[0].message.content
        print('\nModel response:\n')
        print(content)
        sanitized, info = sanitize_response(content, 'id')
        if info.get('sanitized'):
            print('\nSanitized response:\n')
            print(sanitized)
            print('\nSanitization info:', info)
    except Exception as e:
        print('ERROR calling Groq:', e)

print('\nIndonesian test run complete.')
