from datetime import date

from conversation import build_system_prompt, clear_chat_state, initialize_chat_state, trim_history
from topics import TOPICS, build_topic_prompt, topic_followups


def test_all_topic_prompts_are_localized_and_season_uses_date():
    for topic in TOPICS:
        assert build_topic_prompt(topic, "en", date(2026, 10, 9))
        assert build_topic_prompt(topic, "zh", date(2026, 10, 9))
        assert build_topic_prompt(topic, "id", date(2026, 10, 9))
    assert "2026-10-09" in build_topic_prompt("seasonal", "en", date(2026, 10, 9))


def test_followups_are_three_and_localized():
    for topic in TOPICS:
        for lang in ("en", "zh", "id"):
            assert len(topic_followups(topic, lang)) == 3


def test_history_trimming_keeps_recent_turns_and_system_prompt_is_separate():
    history = [
        {"role": "user", "content": "old" * 10},
        {"role": "assistant", "content": "older answer" * 10},
        {"role": "user", "content": "new question"},
    ]
    assert trim_history(history, max_chars=30) == [{"role": "user", "content": "new question"}]
    system = build_system_prompt("safety", "Active category: herbs", "English only", "KB context")
    assert "Active category: herbs" in system
    assert "safety" in system


def test_clear_resets_only_conversation_fields():
    state = {"messages": [{"role": "user", "content": "hi"}], "active_topic": "herbs", "lang": "zh", "prompt_trigger": "x"}
    clear_chat_state(state)
    initialize_chat_state(state)
    assert state["messages"] == []
    assert state["active_topic"] is None
    assert state["lang"] == "zh"
    assert "prompt_trigger" not in state
