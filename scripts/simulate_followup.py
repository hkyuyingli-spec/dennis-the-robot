import os
import sys
# ensure project root on path
sys.path.insert(0, os.getcwd())
from nutribot.rag import (
    load_tcm_constitutions,
    load_tcm_herbs_formulas,
    find_relevant_constitutions,
    find_relevant_herbs_formulas,
    build_rag_context,
    generate_followup_suggestions,
)
from nutribot.safety import sanitize_response

prompt = "I'm always tired and catch colds easily"
print(f"Prompt: {prompt}\n")
consts = load_tcm_constitutions()
herbs = load_tcm_herbs_formulas()
matched_constitutions = find_relevant_constitutions(prompt, consts, current_lang='en')
matched_herbs = find_relevant_herbs_formulas(prompt, herbs, matched_constitutions=matched_constitutions, current_lang='en')

print('Matched Constitutions:', [c.get('name_english') for c in matched_constitutions])
print('Matched Herbs/Formulas:', [h.get('name_english') for h in matched_herbs])

rag_context = build_rag_context(matched_constitutions, matched_herbs)
print('\nRAG Context (truncated):')
print(rag_context[:1000])

# Mock model response (simulate a reasonable assistant reply based on rag_context)
mock_response = ""
if matched_constitutions:
    mock_response += "Based on your symptoms, you may have Qi deficiency (Qi-Xu) which often presents with fatigue and susceptibility to colds. "
if matched_herbs:
    mock_response += "Recommended supportive herbs include Astragalus (Huangqi) which may help strengthen Qi. "
mock_response += "⚕️ For educational purposes only."

print('\nMock model response:')
print(mock_response)

sanitized, info = sanitize_response(mock_response, 'en')
print('\nSanitized response:')
print(sanitized)
print('\nSanitization info:', info)

# Generate follow-up suggestions
followups = generate_followup_suggestions(matched_constitutions, matched_herbs, prompt, lang='en')
print('\nGenerated follow-up suggestions:')
for f in followups:
    print('-', f)

# Simulate clicking the first follow-up
if followups:
    clicked = followups[0]
    print('\nSimulating click on first suggestion:')
    print('Clicked suggestion:', clicked)
    # This would be sent as the next user prompt in the app
    next_prompt = clicked
    print('Next prompt to be sent to the model:', next_prompt)
else:
    print('\nNo follow-ups generated.')
