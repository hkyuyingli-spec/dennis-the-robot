import pytest

from nutribot.rag import (
    cancer_personal_redirect_response,
    is_personal_symptom_query,
)


@pytest.mark.parametrize(
    "prompt",
    [
        "What foods should I eat for Qi-Deficiency?",
        "What is Jing deficiency?",
        "How can I improve energy?",
        "How can I sleep better?",
        "What is Qi?",
        "Explain Shen",
        "Describe Jing",
        "What does blood stasis mean?",
        "What foods help with Yin deficiency or Yang excess?",
        "What is cancer?",
        "What are symptoms of breast cancer?",
        "How can I prevent cancer?",
        "What foods help prevent cancer?",
        "How is cancer diagnosed?",
        "How is cancer treated?",
        "What should I eat during cancer treatment?",
        "How do I support a family member with cancer?",
        "What are symptoms of X?",
        "Symptoms of breast cancer",
    ],
)
def test_general_education_questions_are_not_personal_symptom_queries(prompt):
    assert not is_personal_symptom_query(prompt)


@pytest.mark.parametrize(
    "prompt",
    [
        "I have chest pain and can't breathe",
        "I was diagnosed with cancer, what should I eat?",
        "My mole is bleeding",
        "I feel severe pain",
        "I have a lump in my breast",
        "I was diagnosed with cancer",
        "Should I stop my chemo?",
        "Should I take this supplement with my cancer treatment?",
        "I'm having chest pain",
    ],
)
def test_personal_symptoms_diagnoses_decisions_and_emergencies_redirect(prompt):
    assert is_personal_symptom_query(prompt)


def test_redirect_mentions_oncologist_only_for_cancer_related_queries():
    assert "oncologist" not in cancer_personal_redirect_response("My mole is bleeding")
    assert "oncologist" in cancer_personal_redirect_response(
        "I was diagnosed with cancer"
    )
    assert "oncologist" not in cancer_personal_redirect_response(
        "Should I stop my chemo?"
    )
