from backend.chat import answer_chat


def test_personal_symptom_is_redirected_without_calling_provider():
    provider_called = False

    def get_client():
        nonlocal provider_called
        provider_called = True
        raise AssertionError("provider must not be called for a personal symptom")

    response = answer_chat(
        messages=[{"role": "user", "content": "I have a lump in my breast"}],
        language="en",
        get_client=get_client,
        wrap_client=lambda client, _language: client,
    )

    assert "own health situation" in response["reply"]
    assert provider_called is False


def test_general_cancer_education_is_not_redirected(monkeypatch):
    called = []

    class FakeOrchestrator:
        def __init__(self, _client, model):
            assert model

        def respond(self, prompt, context):
            called.append((prompt, context))
            return "Cancer education answer."

    monkeypatch.setattr("backend.chat.AgentOrchestrator", FakeOrchestrator)
    monkeypatch.setattr("backend.chat._retrieved_knowledge", lambda _prompt, _language: "")
    monkeypatch.setattr("backend.chat.find_passages", lambda *_args, **_kwargs: [])

    response = answer_chat(
        messages=[{"role": "user", "content": "What is cancer?"}],
        language="en",
        get_client=lambda: object(),
        wrap_client=lambda client, _language: client,
    )

    assert response == {
        "reply": "Cancer education answer.",
        "classical_reference_used": False,
    }
    assert called[0][0] == "What is cancer?"


def test_classical_context_includes_bilingual_passages_and_disclaimer(monkeypatch):
    captured = {}
    passage = {
        "id": "wj-001",
        "theme": "seasonal_balance",
        "text_zh": "四時調攝。",
        "text_en": "Adapt daily habits to the seasons.",
    }

    class FakeOrchestrator:
        def __init__(self, _client, model):
            assert model

        def respond(self, prompt, context):
            captured.update(context)
            return "Traditional philosophy answer."

    monkeypatch.setattr("backend.chat.AgentOrchestrator", FakeOrchestrator)
    monkeypatch.setattr("backend.chat._retrieved_knowledge", lambda _prompt, _language: "")
    monkeypatch.setattr("backend.chat.find_passages", lambda *_args, **_kwargs: [passage])
    monkeypatch.setattr("backend.chat.get_disclaimer", lambda: "Traditional text note.")

    result = answer_chat(
        messages=[{"role": "user", "content": "Waijing seasonal balance"}],
        language="en",
        get_client=lambda: object(),
        wrap_client=lambda client, _language: client,
    )

    assert result["classical_reference_used"] is True
    assert "ZH: 四時調攝。" in captured["classical_reference"][0]
    assert "EN: Adapt daily habits to the seasons." in captured["classical_reference"][0]
    assert captured["classical_disclaimer"] == "Traditional text note."
