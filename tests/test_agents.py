from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from nutribot.agents import (
    AGENT_KEYWORDS,
    COORDINATOR_PROMPT,
    SPECIALIST_PROMPTS,
    AgentOrchestrator,
)


def fake_response(content):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def make_client(responses):
    create = Mock(side_effect=[fake_response(text) for text in responses])
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create)
        )
    )
    return client


def test_respond_calls_matching_specialist_and_coordinator():
    client = make_client(["TCM draft", "Nutrition draft", "Combined answer"])
    orchestrator = AgentOrchestrator(client, model="test-model")

    result = orchestrator.respond(
        "How might ginger herbal tea fit into my diet?",
        context={"preference": "unsweetened"},
    )

    assert result == "Combined answer"
    assert client.chat.completions.create.call_count == 3
    calls = client.chat.completions.create.call_args_list
    assert calls[0].kwargs["messages"][0]["content"] == SPECIALIST_PROMPTS["tcm"]
    assert calls[1].kwargs["messages"][0]["content"] == SPECIALIST_PROMPTS["nutrition"]
    assert calls[2].kwargs["messages"][0]["content"] == COORDINATOR_PROMPT
    assert "unsweetened" in calls[0].kwargs["messages"][1]["content"]
    assert all(call.kwargs["model"] == "test-model" for call in calls)


def test_specialists_have_distinct_prompts_and_keywords():
    assert set(SPECIALIST_PROMPTS) == {"tcm", "nutrition", "exercise", "mental_wellness"}
    assert set(AGENT_KEYWORDS) == set(SPECIALIST_PROMPTS)
    assert len(set(SPECIALIST_PROMPTS.values())) == 4


def test_unmatched_question_uses_general_nutrition_specialist():
    client = make_client(["General draft", "Final answer"])
    result = AgentOrchestrator(client).respond("Tell me something useful.")

    assert result == "Final answer"
    assert client.chat.completions.create.call_count == 2
    assert client.chat.completions.create.call_args_list[0].kwargs["messages"][0]["content"] == SPECIALIST_PROMPTS["nutrition"]


@pytest.mark.parametrize(
    ("message", "agent_name"),
    [
        ("How can I sleep better?", "mental_wellness"),
        ("What exercise should I try?", "exercise"),
    ],
)
def test_routes_distinct_specialists(message, agent_name):
    client = make_client(["Draft", "Final"])
    AgentOrchestrator(client).respond(message)

    assert client.chat.completions.create.call_args_list[0].kwargs["messages"][0]["content"] == SPECIALIST_PROMPTS[agent_name]


def test_invalid_message_and_empty_provider_response_raise():
    with pytest.raises(ValueError):
        AgentOrchestrator(make_client([])).respond("  ")

    client = make_client([""])
    with pytest.raises(RuntimeError, match="empty response"):
        AgentOrchestrator(client).respond("What should I eat?")


def test_provider_errors_are_not_silently_replaced():
    create = Mock(side_effect=RuntimeError("provider failure"))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    with pytest.raises(RuntimeError, match="provider failure"):
        AgentOrchestrator(client).respond("What should I eat?")
