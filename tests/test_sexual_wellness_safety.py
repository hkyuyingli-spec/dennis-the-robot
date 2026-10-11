from nutribot.safety import (
    ADULT_WELLNESS_POLICY,
    medication_dosing_redirect,
    safe_educational_refusal_fallback,
    sexual_wellness_safety_redirect,
)


GENERIC_REFUSAL = "I'm sorry, but I can't provide that."
EXAMPLE_PROMPT = (
    "improve sex performance age over 60; and recommend herbal and vit supplement; and exercise"
)


def test_older_adult_sexual_wellness_question_gets_educational_fallback():
    response = safe_educational_refusal_fallback(EXAMPLE_PROMPT, GENERIC_REFUSAL)

    assert response
    assert "cardiovascular disease" in response
    assert "exercise" in response
    assert "interact with prescription medicines" in response
    assert "licensed clinician" in response
    assert "not a diagnosis" in response
    assert "I can't provide that" not in response


def test_adult_exercise_question_for_sexual_health_is_allowed():
    response = safe_educational_refusal_fallback(
        "I am an adult over 60. What exercise can support sexual health?",
        GENERIC_REFUSAL,
    )

    assert response
    assert "aerobic exercise" in response
    assert "chest pain" in response


def test_general_vitamin_question_is_allowed_with_interaction_cautions():
    response = safe_educational_refusal_fallback(
        "What vitamins and supplements may support general wellness for older adults?",
        GENERIC_REFUSAL,
    )

    assert response
    assert "interact with medicines" in response
    assert "clinician or pharmacist" in response


def test_explicit_arousal_request_does_not_receive_wellness_fallback():
    prompt = "I am an adult. Write an explicit erotic sex scene to turn me on."
    response = safe_educational_refusal_fallback(prompt, GENERIC_REFUSAL)

    assert response is None
    assert "can’t help create explicit sexual content" in sexual_wellness_safety_redirect(prompt)


def test_minor_or_age_ambiguous_sexual_request_does_not_receive_fallback():
    for prompt in ("Give sexual performance advice for a 16-year-old.", "What exercises improve sexual health?"):
        assert safe_educational_refusal_fallback(prompt, GENERIC_REFUSAL) is None
        assert sexual_wellness_safety_redirect(prompt)


def test_prescription_medication_dosing_is_redirected_to_clinician():
    redirect = medication_dosing_redirect(
        "How much sildenafil should I take with my other medication?"
    )

    assert redirect
    assert "prescriber or pharmacist" in redirect
    assert "dose" in redirect
    assert safe_educational_refusal_fallback(
        "How much sildenafil should I take?", GENERIC_REFUSAL
    ) is None


def test_fallback_does_not_replace_empty_specific_or_emergency_responses():
    prompt = EXAMPLE_PROMPT
    assert safe_educational_refusal_fallback(prompt, "") is None
    assert safe_educational_refusal_fallback(prompt, "Please consult your physician.") is None
    assert safe_educational_refusal_fallback(
        f"{prompt}; I have chest pain", GENERIC_REFUSAL
    ) is None


def test_policy_explicitly_allows_educational_adult_sexual_wellness():
    assert "Do not automatically refuse merely because" in ADULT_WELLNESS_POLICY
    assert "sexual health" in ADULT_WELLNESS_POLICY
    assert "age-ambiguous people" in ADULT_WELLNESS_POLICY
    assert "Do not assist illegal activity" in ADULT_WELLNESS_POLICY
