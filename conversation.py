"""Small, testable helpers for NutriBot chat history and prompt context."""
from __future__ import annotations

MAX_HISTORY_CHARS = 12000

def trim_history(messages: list[dict], max_messages: int = 4, assistant_chars: int = 500) -> list[dict]:
    """Send only the newest four turns and bound older assistant text."""
    selected = []
    for message in messages[-max_messages:]:
        content = str(message.get("content", ""))
        if message.get("role") == "assistant" and len(content) > assistant_chars:
            content = content[:assistant_chars].rstrip() + "…"
        selected.append({"role": message["role"], "content": content})
    return selected


def topic_cache_key(topic: str, language: str) -> tuple[str, str]:
    return topic, language if language in ("en", "zh", "id") else "en"


def consume_pending_topic(state):
    """Consume a topic click once so reruns cannot resubmit its starter."""
    return state.pop("pending_topic", None)


def queue_pending_topic(state, topic: str) -> bool:
    """Queue at most one category click until the chat handler consumes it."""
    if state.get("pending_topic") is not None:
        return False
    state["pending_topic"] = {"topic": topic}
    return True

def build_system_prompt(personality: str, topic_context: str, language_directive: str, rag_context: str = "") -> str:
    return "\n\n".join(part for part in (personality, topic_context, language_directive, rag_context) if part)

def initialize_chat_state(state) -> None:
    state.setdefault("messages", [])
    state.setdefault("active_topic", None)
    state.setdefault("session_id", "")
    state.setdefault("pending_topic", None)

def clear_chat_state(state) -> None:
    state["messages"] = []
    state["active_topic"] = None
    state.pop("prompt_trigger", None)
    state.pop("pending_topic_prompt", None)
    state["pending_topic"] = None
